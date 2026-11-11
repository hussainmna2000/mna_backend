"""Property schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.property import PropertyType, PropertyStatus


class PropertyBase(BaseModel):
    title: str
    tagline: str = ""
    type: PropertyType
    status: PropertyStatus = PropertyStatus.upcoming
    location: str = ""
    city: str = "Padiyur Ottapalayam"
    price_starting: str = ""
    price_numeric: float | None = None
    bedrooms: str = ""
    carpet_area: str = ""
    possession_date: str = ""
    completion_percentage: int = 0
    featured: bool = False
    hero_image: str = ""
    rera_id: str = ""
    architect: str = ""
    description: str = ""
    highlights: list = []
    amenities: list = []
    gallery_images: list = []


class PropertyCreate(PropertyBase):
    slug: str


class PropertyUpdate(BaseModel):
    """All fields optional for PATCH."""
    title: str | None = None
    tagline: str | None = None
    type: PropertyType | None = None
    status: PropertyStatus | None = None
    location: str | None = None
    city: str | None = None
    price_starting: str | None = None
    price_numeric: float | None = None
    bedrooms: str | None = None
    carpet_area: str | None = None
    possession_date: str | None = None
    completion_percentage: int | None = None
    featured: bool | None = None
    hero_image: str | None = None
    rera_id: str | None = None
    architect: str | None = None
    description: str | None = None
    highlights: list | None = None
    amenities: list | None = None
    gallery_images: list | None = None
    slug: str | None = None


class PropertyResponse(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    created_at: datetime
    updated_at: datetime


class PropertyListResponse(BaseModel):
    items: list[PropertyResponse]
    total: int
    page: int
    page_size: int
    pages: int
