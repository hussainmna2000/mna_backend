"""Site visit booking routes."""
import math
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.middleware.rate_limit import limiter
from app.models.booking import BookingStatus, SiteVisitBooking
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_booking(request: Request, body: BookingCreate, db: Session = Depends(get_db)):
    """Public endpoint: book a site visit."""
    booking = SiteVisitBooking(**body.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return BookingResponse.model_validate(booking)


@router.get("/my", response_model=BookingListResponse)
def get_my_bookings(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return bookings linked to the authenticated user."""
    query = db.query(SiteVisitBooking).filter(SiteVisitBooking.user_id == current_user.id)
    total = query.count()
    items = query.order_by(SiteVisitBooking.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    pages = math.ceil(total / page_size) if total else 1
    return BookingListResponse(
        items=[BookingResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel the authenticated user's own booking."""
    booking = db.query(SiteVisitBooking).filter(
        SiteVisitBooking.id == booking_id,
        SiteVisitBooking.user_id == current_user.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.status in (BookingStatus.completed, BookingStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status '{booking.status.value}'.",
        )
    booking.status = BookingStatus.cancelled
    db.commit()
    return {"message": "Booking cancelled successfully."}
