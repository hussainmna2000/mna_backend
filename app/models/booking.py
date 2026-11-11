"""Site visit booking model."""
import enum
from datetime import date, datetime
from sqlalchemy import (
    Date, DateTime, Enum, ForeignKey, Integer,
    String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class SiteVisitBooking(Base):
    """Site visit booking by a potential buyer."""

    __tablename__ = "site_visit_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visitor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    visitor_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    visitor_phone: Mapped[str] = mapped_column(String(20), nullable=False)

    property_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    visit_time: Mapped[str] = mapped_column(String(10), nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="bookingstatus"), default=BookingStatus.pending, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional link to registered user
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="bookings")
    user: Mapped["User"] = relationship("User", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<SiteVisitBooking id={self.id} visitor={self.visitor_name} date={self.visit_date}>"
