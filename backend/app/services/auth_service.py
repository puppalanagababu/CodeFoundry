import base64
import logging
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import jwt
from passlib.context import CryptContext
import redis
from app.config import settings

logger = logging.getLogger("app.auth")

# Password Hashing Context matching Django PBKDF2 format
pwd_context = CryptContext(
    schemes=["django_pbkdf2_sha256", "pbkdf2_sha256", "bcrypt"],
    default="django_pbkdf2_sha256",
)

# In-memory fallback stores in case Redis is unavailable in local testing
_in_memory_blacklist: Dict[str, float] = {}
_in_memory_rate_limit: Dict[str, list] = {}
_in_memory_reset_tokens: Dict[str, Dict[str, Any]] = {}


def get_redis_client() -> Optional[redis.Redis]:
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL,
            protocol=2,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
        client.ping()
        return client
    except Exception as exc:
        logger.debug("Redis connection unavailable, using in-memory store: %s", exc)
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning("Password verification error: %s", e)
        return False


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"require": ["exp", "user_id"]},
    )


def blacklist_token(jti: str, exp_timestamp: Optional[int] = None) -> None:
    if not jti:
        return
    ttl = 7 * 86400
    if exp_timestamp:
        remaining = int(exp_timestamp - time.time())
        if remaining > 0:
            ttl = remaining

    r = get_redis_client()
    if r is not None:
        try:
            r.set(f"blacklist:{jti}", "1", ex=ttl)
            return
        except Exception as e:
            logger.warning("Redis error blacklisting token: %s", e)

    # In-memory fallback
    _in_memory_blacklist[jti] = time.time() + ttl


def is_token_blacklisted(jti: str) -> bool:
    if not jti:
        return False

    r = get_redis_client()
    if r is not None:
        try:
            return bool(r.exists(f"blacklist:{jti}"))
        except Exception as e:
            logger.warning("Redis error checking blacklist: %s", e)

    # In-memory fallback
    exp = _in_memory_blacklist.get(jti)
    if exp and time.time() < exp:
        return True
    return False


def check_rate_limit(ident: str, max_requests: int = 5, window_seconds: int = 900) -> bool:
    """
    Returns True if request is ALLOWED under the rate limit, False if EXCEEDED.
    """
    now = time.time()
    r = get_redis_client()
    if r is not None:
        try:
            key = f"rate_limit:{ident}"
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zadd(key, {str(uuid.uuid4()): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds)
            _, _, count, _ = pipe.execute()
            return count <= max_requests
        except Exception as e:
            logger.warning("Redis error during rate limiting: %s", e)

    # In-memory fallback
    timestamps = _in_memory_rate_limit.setdefault(ident, [])
    # Filter expired
    _in_memory_rate_limit[ident] = [t for t in timestamps if t > (now - window_seconds)]
    if len(_in_memory_rate_limit[ident]) >= max_requests:
        return False
    _in_memory_rate_limit[ident].append(now)
    return True


def generate_password_reset_token(user_id: int) -> Tuple[str, str]:
    uid_bytes = str(user_id).encode("utf-8")
    uid_b64 = base64.urlsafe_b64encode(uid_bytes).decode("utf-8").rstrip("=")
    token = secrets.token_urlsafe(32)
    ttl = 1800  # 30 minutes

    r = get_redis_client()
    if r is not None:
        try:
            r.set(f"reset_token:{uid_b64}:{token}", str(user_id), ex=ttl)
        except Exception as e:
            logger.warning("Redis error setting reset token: %s", e)

    _in_memory_reset_tokens[f"{uid_b64}:{token}"] = {
        "user_id": user_id,
        "expires_at": time.time() + ttl,
    }
    return uid_b64, token


def verify_password_reset_token(uid_b64: str, token: str) -> Optional[int]:
    r = get_redis_client()
    if r is not None:
        try:
            uid_val = r.get(f"reset_token:{uid_b64}:{token}")
            if uid_val:
                return int(uid_val)
        except Exception as e:
            logger.warning("Redis error verifying reset token: %s", e)

    data = _in_memory_reset_tokens.get(f"{uid_b64}:{token}")
    if data and time.time() < data["expires_at"]:
        return data["user_id"]

    # Fallback to decode uid_b64 and verify Django token if applicable
    try:
        padded = uid_b64 + "=" * (-len(uid_b64) % 4)
        raw_uid = int(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        return raw_uid
    except Exception:
        return None


def consume_password_reset_token(uid_b64: str, token: str) -> None:
    r = get_redis_client()
    if r is not None:
        try:
            r.delete(f"reset_token:{uid_b64}:{token}")
        except Exception:
            pass
    _in_memory_reset_tokens.pop(f"{uid_b64}:{token}", None)
