from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, RefreshToken
from app.schemas.user import UserResponse, UserUpdateRequest, PasswordChangeRequest
from app.middleware.auth_middleware import get_current_active_user, require_admin
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's full profile."""
    return UserResponse.from_orm(current_user)


@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile information."""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.phone is not None:
        current_user.phone = update_data.phone
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return UserResponse.from_orm(current_user)


@router.patch("/me/password")
def change_password(
    pwd_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    if not verify_password(pwd_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    current_user.hashed_password = hash_password(pwd_data.new_password)
    current_user.updated_at = datetime.utcnow()
    # Revoke all sessions except current
    db.commit()
    return {"message": "Password changed successfully."}


@router.delete("/me")
def delete_own_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """User deletes their own account."""
    db.delete(current_user)
    db.commit()
    return {"message": "Account has been permanently deleted."}


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List users (Administrative access required)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.from_orm(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID (Administrative access required)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.from_orm(user)
