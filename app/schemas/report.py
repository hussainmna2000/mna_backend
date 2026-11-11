from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ReportCreateRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    suspicious_phone: Optional[str] = None
    suspicious_url: Optional[str] = None
    suspicious_email: Optional[str] = None
    evidence_url: Optional[str] = None
    financial_loss: Optional[float] = 0.0


class ReportUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    suspicious_phone: Optional[str] = None
    suspicious_url: Optional[str] = None
    suspicious_email: Optional[str] = None
    evidence_url: Optional[str] = None
    financial_loss: Optional[float] = None


class ReportStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|under_review|verified|rejected|resolved)$")
    admin_notes: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    category: str
    title: str
    description: str
    suspicious_phone: Optional[str] = None
    suspicious_url: Optional[str] = None
    suspicious_email: Optional[str] = None
    evidence_url: Optional[str] = None
    financial_loss: float
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    total: int
    page: int
    pages: int
    items: List[ReportResponse]
