from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PhoneDetectionRequest(BaseModel):
    phone_number: str = Field(..., min_length=5, max_length=30)
    context: Optional[str] = None


class MessageDetectionRequest(BaseModel):
    message_text: str = Field(..., min_length=3)
    channel: Optional[str] = "sms"  # 'sms', 'whatsapp', 'telegram'


class UrlDetectionRequest(BaseModel):
    url: str = Field(..., min_length=4)


class EmailDetectionRequest(BaseModel):
    email_text: Optional[str] = None
    sender_email: Optional[str] = None
    subject: Optional[str] = None


class AnalyzeDetectionRequest(BaseModel):
    content: str = Field(..., min_length=2)
    type: str = "general"  # 'phone', 'message', 'url', 'email', 'transaction', 'general'


class DetectionResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    category: str
    query_target: str
    risk_score: float
    risk_level: str  # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    verdict: str
    threat_indicators: Optional[List[str]] = None
    explanation: Optional[str] = None
    recommendations: Optional[List[str]] = None
    metadata_info: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DetectionListResponse(BaseModel):
    total: int
    items: List[DetectionResponse]
