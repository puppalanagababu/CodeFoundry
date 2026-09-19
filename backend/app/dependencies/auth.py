from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import decode_token, is_token_blacklisted

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Given token not valid for any token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Given token not valid for any token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Given token not valid for any token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is blacklisted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def require_role(*allowed_roles) -> Callable[[User], User]:
    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple, set)):
        roles_set = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles[0]}
    else:
        roles_set = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles}

    def role_checker(user: User = Depends(get_current_user)) -> User:
        user_role = getattr(user, "role", UserRole.STUDENT.value)
        is_admin = (user_role == UserRole.ADMIN.value) or user.is_staff or user.is_superuser
        if user_role in roles_set or is_admin:
            return user
        detail_msg = (
            "You do not have permission to access the recruiter dashboard."
            if UserRole.RECRUITER.value in roles_set
            else "You do not have permission to perform this action."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_msg,
        )

    return role_checker
