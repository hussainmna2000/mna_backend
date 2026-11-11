"""Booking schemas."""
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    visitor_name: str
    visitor_email: EmailStr
    visitor_phone: str
    property_id: int
    visit_date: date
    visit_time: str
    notes: str | None = None


class BookingUpdate(BaseModel):
    status: BookingStatus | None = None
    admin_notes: str | None = None
    visit_date: date | None = None
    visit_time: str | None = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visitor_name: str
    visitor_email: str
    visitor_phone: str
    property_id: int
    visit_date: date
    visit_time: str
    status: BookingStatus
    notes: str | None
    admin_notes: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int
    pages: int
