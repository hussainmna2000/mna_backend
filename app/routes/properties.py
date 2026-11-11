"""Property listing routes (public)."""
import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property, PropertyStatus, PropertyType
from app.schemas.property import PropertyListResponse, PropertyResponse

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("", response_model=PropertyListResponse)
def list_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    type: PropertyType | None = None,
    status: PropertyStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all properties with optional filters and pagination."""
    query = db.query(Property)
    if type:
        query = query.filter(Property.type == type)
    if status:
        query = query.filter(Property.status == status)

    total = query.count()
    items = query.order_by(Property.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    pages = math.ceil(total / page_size) if total else 1

    return PropertyListResponse(
        items=[PropertyResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/featured", response_model=list[PropertyResponse])
def get_featured_properties(db: Session = Depends(get_db)):
    """Return all featured properties."""
    items = db.query(Property).filter(Property.featured.is_(True)).all()
    return [PropertyResponse.model_validate(p) for p in items]


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    """Get a single property by ID."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    return PropertyResponse.model_validate(prop)
