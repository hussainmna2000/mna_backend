from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, RefreshToken
from app.models.activity_log import ActivityLog
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserPublicResponse,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_customer_id,
)
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request_data: UserRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == request_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    customer_id = generate_customer_id()
    hashed = hash_password(request_data.password)

    new_user = User(
        email=request_data.email.lower(),
        full_name=request_data.full_name,
        phone=request_data.phone,
        customer_id=customer_id,
        hashed_password=hashed,
        role="user",
        status="active",
        is_verified=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue tokens
    access_token = create_access_token({"sub": str(new_user.id), "role": new_user.role})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})

    db_refresh = RefreshToken(
        user_id=new_user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(db_refresh)

    # Log activity
    ip = request.client.host if request.client else None
    log = ActivityLog(
        admin_id=None,
        action="user_registered",
        entity_type="user",
        entity_id=new_user.id,
        details={"email": new_user.email},
        ip_address=ip,
    )
    db.add(log)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserPublicResponse.from_orm(new_user),
    )


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact security administration.",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(db_refresh)

    ip = request.client.host if request.client else None
    log = ActivityLog(
        admin_id=user.id if user.role in ["admin", "superadmin"] else None,
        action="user_login",
        entity_type="user",
        entity_id=user.id,
        details={"role": user.role},
        ip_address=ip,
    )
    db.add(log)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserPublicResponse.from_orm(user),
    )


@router.post("/refresh")
def refresh_token_endpoint(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Rotate and refresh JWT access token."""
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = payload.get("sub")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    token_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == data.refresh_token, RefreshToken.is_revoked == False)
        .first()
    )
    if not token_record or token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account inaccessible")

    # Rotate token
    token_record.is_revoked = True
    new_access = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    new_db_refresh = RefreshToken(
        user_id=user.id,
        token=new_refresh,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(new_db_refresh)
    db.commit()

    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke all active refresh tokens for the current user."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()
    return {"message": "Logged out successfully. All sessions invalidated."}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset link. Returns standard success response to prevent user enumeration."""
    # Production implementation: Generate reset token and email user
    return {"message": "If an account exists with that email address, password reset instructions have been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using secure token."""
    try:
        payload = decode_token(data.token)
        user_id = payload.get("sub")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    user.updated_at = datetime.utcnow()
    # Revoke all existing sessions
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
    db.commit()
    return {"message": "Password successfully updated. Please login with your new credentials."}


@router.get("/me", response_model=UserPublicResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's profile."""
    return UserPublicResponse.from_orm(current_user)
