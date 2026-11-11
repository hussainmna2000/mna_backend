"""Inquiry routes."""
import math
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.middleware.rate_limit import limiter
from app.models.inquiry import Inquiry
from app.models.user import User
from app.schemas.inquiry import InquiryCreate, InquiryListResponse, InquiryResponse

router = APIRouter(prefix="/inquiries", tags=["Inquiries"])


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def submit_inquiry(request: Request, body: InquiryCreate, db: Session = Depends(get_db)):
    """Public endpoint: submit a contact form inquiry."""
    inquiry = Inquiry(**body.model_dump())
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return InquiryResponse.model_validate(inquiry)


@router.get("/my", response_model=InquiryListResponse)
def get_my_inquiries(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return inquiries linked to the authenticated user."""
    query = db.query(Inquiry).filter(Inquiry.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Inquiry.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    pages = math.ceil(total / page_size) if total else 1
    return InquiryListResponse(
        items=[InquiryResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
