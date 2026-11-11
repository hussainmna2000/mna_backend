"""Inquiry model for contact form submissions."""
import enum
from datetime import datetime
from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer,
    String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class InquiryStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    closed = "closed"


class Inquiry(Base):
    """Contact form inquiry from website visitors."""

    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interest: Mapped[str] = mapped_column(String(255), nullable=False, default="general")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[InquiryStatus] = mapped_column(
        Enum(InquiryStatus, name="inquirystatus"), default=InquiryStatus.new, nullable=False
    )
    source: Mapped[str] = mapped_column(String(100), default="contact_form", nullable=False)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional link to a registered user
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
    user: Mapped["User"] = relationship("User", back_populates="inquiries")

    def __repr__(self) -> str:
        return f"<Inquiry id={self.id} email={self.email} status={self.status}>"
