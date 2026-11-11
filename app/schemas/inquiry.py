"""Inquiry schemas."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.inquiry import InquiryStatus


class InquiryCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    interest: str = "general"
    message: str


class InquiryUpdate(BaseModel):
    status: InquiryStatus | None = None
    admin_notes: str | None = None


class InquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str | None
    interest: str
    message: str
    status: InquiryStatus
    source: str
    admin_notes: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime


class InquiryListResponse(BaseModel):
    items: list[InquiryResponse]
    total: int
    page: int
    page_size: int
    pages: int
