"""Authentication service: register, login, token lifecycle."""
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, RefreshToken, UserStatus
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_customer_id,
)


def register_user(db: Session, full_name: str, email: str, phone: str | None, password: str) -> User:
    """Create a new client user account."""
    # Ensure unique email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Generate a unique customer_id (retry on collision)
    for _ in range(10):
        customer_id = generate_customer_id()
        if not db.query(User).filter(User.customer_id == customer_id).first():
            break

    user = User(
        customer_id=customer_id,
        full_name=full_name,
        email=email,
        phone=phone,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """Authenticate by email or customer_id + password."""
    # Try email first, then customer_id
    user = db.query(User).filter(User.email == identifier).first()
    if not user:
        user = db.query(User).filter(User.customer_id == identifier).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials.",
        )
    if user.status == UserStatus.suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
        )
    return user


def create_tokens_for_user(db: Session, user: User) -> tuple[str, str]:
    """Create access + refresh tokens and persist the refresh token."""
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token_str = create_refresh_token(data={"sub": str(user.id)})

    # Store the refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=expires_at,
    )
    db.add(rt)

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return access_token, refresh_token_str


def rotate_refresh_token(db: Session, old_token: str) -> tuple[str, str]:
    """Revoke the old refresh token and issue new pair."""
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )
    try:
        payload = decode_token(old_token)
        if payload.get("type") != "refresh":
            raise invalid_exc
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise invalid_exc

    rt = db.query(RefreshToken).filter(
        RefreshToken.token == old_token,
        RefreshToken.is_revoked.is_(False),
    ).first()
    if not rt or rt.expires_at < datetime.now(timezone.utc):
        raise invalid_exc

    # Revoke old token
    rt.is_revoked = True
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise invalid_exc

    return create_tokens_for_user(db, user)


def revoke_refresh_token(db: Session, token: str) -> None:
    """Revoke a specific refresh token (logout)."""
    rt = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if rt:
        rt.is_revoked = True
        db.commit()
