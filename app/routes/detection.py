from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.detection import ScamDetection
from app.models.user import User
from app.schemas.detection import (
    PhoneDetectionRequest,
    MessageDetectionRequest,
    UrlDetectionRequest,
    EmailDetectionRequest,
    AnalyzeDetectionRequest,
    DetectionResponse,
    DetectionListResponse,
)
from app.services.detection_service import ScamDetectionEngine
from app.middleware.auth_middleware import get_optional_user, get_current_active_user

router = APIRouter(prefix="/detection", tags=["Scam Detection"])


def _save_and_return_detection(result: dict, request: Request, user: Optional[User], db: Session) -> DetectionResponse:
    ip = request.client.host if request.client else None
    record = ScamDetection(
        user_id=user.id if user else None,
        category=result["category"],
        query_target=result["query_target"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        verdict=result["verdict"],
        threat_indicators=result.get("threat_indicators"),
        explanation=result.get("explanation"),
        recommendations=result.get("recommendations"),
        metadata_info=result.get("metadata_info"),
        ip_address=ip,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return DetectionResponse.from_orm(record)


@router.post("/phone", response_model=DetectionResponse)
def detect_phone(
    data: PhoneDetectionRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Analyze a phone number for spam, robocall, or known scam patterns."""
    analysis = ScamDetectionEngine.analyze_phone(data.phone_number, data.context or "")
    return _save_and_return_detection(analysis, request, user, db)


@router.post("/message", response_model=DetectionResponse)
def detect_message(
    data: MessageDetectionRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Analyze SMS or WhatsApp text for phishing and scam indicators."""
    analysis = ScamDetectionEngine.analyze_message(data.message_text, data.channel or "sms")
    return _save_and_return_detection(analysis, request, user, db)


@router.post("/url", response_model=DetectionResponse)
def detect_url(
    data: UrlDetectionRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Analyze a URL / domain for malicious phishing, homographs, or fake portals."""
    analysis = ScamDetectionEngine.analyze_url(data.url)
    return _save_and_return_detection(analysis, request, user, db)


@router.post("/email", response_model=DetectionResponse)
def detect_email(
    data: EmailDetectionRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Analyze an email address or message content for fraud or spoofing."""
    analysis = ScamDetectionEngine.analyze_email(
        email_text=data.email_text or "",
        sender_email=data.sender_email or "",
        subject=data.subject or ""
    )
    return _save_and_return_detection(analysis, request, user, db)


@router.post("/analyze", response_model=DetectionResponse)
def detect_analyze(
    data: AnalyzeDetectionRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """General AI / multi-vector detection endpoint supporting text, transactions, or contacts."""
    analysis = ScamDetectionEngine.analyze_general(data.content, data.type)
    return _save_and_return_detection(analysis, request, user, db)


@router.get("/history", response_model=DetectionListResponse)
def get_detection_history(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get scan history for the authenticated user."""
    query = db.query(ScamDetection).filter(ScamDetection.user_id == user.id)
    total = query.count()
    items = query.order_by(ScamDetection.created_at.desc()).offset(skip).limit(limit).all()
    return DetectionListResponse(total=total, items=[DetectionResponse.from_orm(item) for item in items])


@router.get("/{detection_id}", response_model=DetectionResponse)
def get_detection_by_id(
    detection_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Retrieve details for a specific detection scan."""
    record = db.query(ScamDetection).filter(ScamDetection.id == detection_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection report not found")
    # If detection has an owner, check authorization unless user is admin
    if record.user_id and (not user or (user.id != record.user_id and user.role not in ["admin", "superadmin"])):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return DetectionResponse.from_orm(record)
