"""Property / Project model."""
import enum
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, Enum, Float, Integer,
    String, Text, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PropertyType(str, enum.Enum):
    bhk_1 = "1bhk"
    bhk_2 = "2bhk"
    custom = "custom"
    land = "land"


class PropertyStatus(str, enum.Enum):
    upcoming = "upcoming"
    under_construction = "under_construction"
    ready_to_move = "ready_to_move"


class Property(Base):
    """Real estate property / project listing."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    tagline: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType, name="propertytype"), nullable=False
    )
    status: Mapped[PropertyStatus] = mapped_column(
        Enum(PropertyStatus, name="propertystatus"), default=PropertyStatus.upcoming, nullable=False
    )

    location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Padiyur Ottapalayam")
    price_starting: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    price_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    bedrooms: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    carpet_area: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    possession_date: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    hero_image: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    rera_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    architect: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # JSON fields
    highlights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    amenities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    gallery_images: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    assigned_clients: Mapped[list["User"]] = relationship(
        "User", back_populates="project", foreign_keys="User.project_id"
    )
    bookings: Mapped[list["SiteVisitBooking"]] = relationship(
        "SiteVisitBooking", back_populates="property", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Property id={self.id} title={self.title} status={self.status}>"
