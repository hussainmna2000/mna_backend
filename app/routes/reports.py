from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.report import ScamReport
from app.models.user import User
from app.schemas.report import (
    ReportCreateRequest,
    ReportUpdateRequest,
    ReportResponse,
    ReportListResponse,
)
from app.middleware.auth_middleware import get_current_active_user, get_optional_user

router = APIRouter(prefix="/reports", tags=["Scam Reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def submit_report(
    data: ReportCreateRequest,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Submit a scam report for community awareness and investigation."""
    report = ScamReport(
        user_id=user.id if user else None,
        category=data.category,
        title=data.title,
        description=data.description,
        suspicious_phone=data.suspicious_phone,
        suspicious_url=data.suspicious_url,
        suspicious_email=data.suspicious_email,
        evidence_url=data.evidence_url,
        financial_loss=data.financial_loss or 0.0,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportResponse.from_orm(report)


@router.get("", response_model=ReportListResponse)
def list_reports(
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    List reports.
    If authenticated non-admin user requests /reports, they see verified public reports or their own.
    If admin requests, all reports are returned.
    """
    query = db.query(ScamReport)
    
    # Non-admins only see verified community reports or their own
    is_admin = user and user.role in ["admin", "superadmin"]
    if not is_admin:
        if user:
            query = query.filter((ScamReport.status == "verified") | (ScamReport.user_id == user.id))
        else:
            query = query.filter(ScamReport.status == "verified")

    if category:
        query = query.filter(ScamReport.category == category)
    if status_filter and is_admin:
        query = query.filter(ScamReport.status == status_filter)

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    items = query.order_by(ScamReport.created_at.desc()).offset(offset).limit(limit).all()

    return ReportListResponse(
        total=total,
        page=page,
        pages=pages,
        items=[ReportResponse.from_orm(item) for item in items]
    )


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_details(
    report_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Retrieve details for a single scam report."""
    report = db.query(ScamReport).filter(ScamReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    # Access check: public verified reports are viewable by anyone; unverified by owner or admin
    is_admin = user and user.role in ["admin", "superadmin"]
    is_owner = user and report.user_id == user.id
    if report.status != "verified" and not is_admin and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ReportResponse.from_orm(report)


@router.patch("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: int,
    data: ReportUpdateRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update report details. Only report owner or admin can update."""
    report = db.query(ScamReport).filter(ScamReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    is_admin = user.role in ["admin", "superadmin"]
    if report.user_id != user.id and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if data.title is not None:
        report.title = data.title
    if data.description is not None:
        report.description = data.description
    if data.suspicious_phone is not None:
        report.suspicious_phone = data.suspicious_phone
    if data.suspicious_url is not None:
        report.suspicious_url = data.suspicious_url
    if data.suspicious_email is not None:
        report.suspicious_email = data.suspicious_email
    if data.evidence_url is not None:
        report.evidence_url = data.evidence_url
    if data.financial_loss is not None:
        report.financial_loss = data.financial_loss

    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return ReportResponse.from_orm(report)


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a report. Only owner or admin can delete."""
    report = db.query(ScamReport).filter(ScamReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    is_admin = user.role in ["admin", "superadmin"]
    if report.user_id != user.id and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully."}
