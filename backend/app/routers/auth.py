import base64
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
import jwt
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import (
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
)
from app.services.auth_service import (
    blacklist_token,
    check_rate_limit,
    consume_password_reset_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    hash_password,
    is_token_blacklisted,
    verify_password,
    verify_password_reset_token,
)

logger = logging.getLogger("app.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    if not request:
        return "unknown"
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return getattr(request.client, "host", "unknown") if request.client else "unknown"


def sanitize_log_value(value: Any) -> str:
    if not value:
        return ""
    return str(value).replace("\r", "").replace("\n", "").replace("\t", "").strip()[:150]


@router.post("/register/", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    clean_username = payload.username.strip()
    existing_user = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"username": ["A user with that username already exists."]},
        )

    new_user = User(
        username=clean_username,
        email=payload.email.strip() if payload.email else "",
        password=hash_password(payload.password),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserRegisterResponse(
        message="User registered successfully.",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login/", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(request: Request, payload: UserLoginRequest, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    clean_user = sanitize_log_value(payload.username)

    # Rate limiting: 5 requests per 15 mins (900 seconds) per IP & username
    rate_key = f"login_{ip}_{clean_user.lower()}"
    if not check_rate_limit(rate_key, max_requests=5, window_seconds=900):
        logger.warning("Login rate limit exceeded for ident: %s", rate_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Request was throttled. Expected available in 900 seconds.",
        )

    user = db.query(User).filter(func.lower(User.username) == payload.username.strip().lower()).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password):
        logger.warning("Login authentication failed for user: %s (IP: %s)", clean_user, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active account found with the given credentials",
        )

    logger.info("Login successful for user: %s (IP: %s)", clean_user, ip)
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    return TokenResponse(
        access=access_token,
        refresh=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh/", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
@router.post("/refresh", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
def refresh_token(payload: TokenRefreshRequest, db: Session = Depends(get_db)):
    raw_token = payload.refresh
    try:
        decoded = decode_token(raw_token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )

    if decoded.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )

    jti = decoded.get("jti")
    if not jti or is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )

    user_id = decoded.get("user_id")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )

    # Rotate refresh token: blacklist old token and issue new pair
    blacklist_token(jti, decoded.get("exp"))
    new_access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id, user.role)

    return TokenRefreshResponse(
        access=new_access,
        refresh=new_refresh,
    )


@router.post("/logout/", response_model=MessageResponse, status_code=status.HTTP_200_OK)
@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout(request: Request, payload: LogoutRequest):
    ip = get_client_ip(request)
    if not payload.refresh:
        logger.warning("Logout failed: missing refresh token (IP: %s)", ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required.",
        )

    try:
        decoded = decode_token(payload.refresh)
        jti = decoded.get("jti")
        if jti:
            blacklist_token(jti, decoded.get("exp"))
        logger.info("Logout completed successfully (IP: %s)", ip)
        return MessageResponse(message="Logged out successfully.")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        logger.warning("Logout failed: invalid or expired refresh token (IP: %s)", ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired refresh token.",
        )


@router.get("/me/", response_model=UserResponse, status_code=status.HTTP_200_OK)
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/password-reset/", response_model=MessageResponse, status_code=status.HTTP_200_OK)
@router.post("/password-reset", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def password_reset_request(request: Request, payload: PasswordResetRequest, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    clean_email = sanitize_log_value(payload.email)

    rate_key = f"password_reset_{ip}_{clean_email.lower()}"
    if not check_rate_limit(rate_key, max_requests=5, window_seconds=900):
        logger.warning("Password reset rate limit exceeded for ident: %s", rate_key)
        # Safe 200 response to prevent enumeration
        return MessageResponse(detail="If an account exists for this email, password reset instructions have been sent.")

    user = db.query(User).filter(func.lower(User.email) == payload.email.strip().lower(), User.is_active == True).first()
    if user:
        uid_b64, reset_token = generate_password_reset_token(user.id)
        logger.info("Password reset requested for user ID: %s (IP: %s)", user.id, ip)

    return MessageResponse(detail="If an account exists for this email, password reset instructions have been sent.")


@router.post("/password-reset/confirm/", response_model=MessageResponse, status_code=status.HTTP_200_OK)
@router.post("/password-reset/confirm", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def password_reset_confirm(request: Request, payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    user_id = verify_password_reset_token(payload.uid, payload.token)
    if not user_id:
        logger.warning("Password reset failed: invalid or expired token (IP: %s)", ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Invalid or expired password reset token."},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        logger.warning("Password reset failed: user not found (IP: %s)", ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Invalid or expired password reset token."},
        )

    user.password = hash_password(payload.new_password)
    db.commit()
    consume_password_reset_token(payload.uid, payload.token)
    logger.info("Password reset completed successfully for user ID: %s (IP: %s)", user.id, ip)

    return MessageResponse(message="Password has been reset successfully.")
