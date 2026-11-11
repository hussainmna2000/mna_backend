from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: int
    customer_id: Optional[str] = None
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str
    status: str
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(active|suspended|pending)$")


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(user|admin|superadmin)$")
