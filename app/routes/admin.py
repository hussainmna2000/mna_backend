import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.detection import ScamDetection
from app.models.report import ScamReport
from app.models.activity_log import ActivityLog
from app.schemas.user import UserResponse, UserStatusUpdateRequest, UserRoleUpdateRequest
from app.schemas.report import ReportResponse, ReportStatusUpdateRequest
from app.schemas.detection import DetectionResponse
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminAnalyticsResponse,
    ActivityLogResponse,
    PaginatedActivityLogs,
    SystemHealthResponse,
    SystemStatisticsResponse,
)
from app.middleware.auth_middleware import require_admin, require_superadmin
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Administrative Control"])

_SERVER_START_TIME = time.time()


def _log_admin_action(db: Session, admin_id: int, action: str, entity_type: str, entity_id: Optional[int], details: Optional[Dict], request: Request):
    ip = request.client.host if request.client else None
    log = ActivityLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip,
    )
    db.add(log)
    db.commit()


# ---------------------------------------------------------
# Dashboard & Analytics
# ---------------------------------------------------------
@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve complete executive dashboard statistics from the database."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    suspended_users = db.query(User).filter(User.status == "suspended").count()

    total_reports = db.query(ScamReport).count()
    pending_reports = db.query(ScamReport).filter(ScamReport.status == "pending").count()
    resolved_reports = db.query(ScamReport).filter(ScamReport.status == "resolved").count()

    total_detections = db.query(ScamDetection).count()
    high_risk_detections = (
        db.query(ScamDetection)
        .filter(ScamDetection.risk_level.in_(["HIGH", "CRITICAL"]))
        .count()
    )

    cat_counts = (
        db.query(ScamDetection.category, func.count(ScamDetection.id))
        .group_by(ScamDetection.category)
        .all()
    )
    category_distribution = {cat or "general": count for cat, count in cat_counts}

    recent_logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "id": log.id,
            "admin_id": log.admin_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in recent_logs
    ]

    return AdminDashboardResponse(
        total_users=total_users,
        active_users=active_users,
        suspended_users=suspended_users,
        total_reports=total_reports,
        pending_reports=pending_reports,
        resolved_reports=resolved_reports,
        total_detections=total_detections,
        high_risk_detections=high_risk_detections,
        category_distribution=category_distribution,
        recent_activity=recent_activity,
    )


@router.get("/analytics", response_model=AdminAnalyticsResponse)
def get_admin_analytics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve full analytics and trends over the past 30 days."""
    now = datetime.utcnow()

    # Daily scam detection trends (past 14 days)
    detection_trends = []
    scam_trends = []
    user_growth = []

    for i in range(13, -1, -1):
        day = now - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        label = day_start.strftime("%b %d")

        det_count = (
            db.query(ScamDetection)
            .filter(ScamDetection.created_at >= day_start, ScamDetection.created_at < day_end)
            .count()
        )
        rep_count = (
            db.query(ScamReport)
            .filter(ScamReport.created_at >= day_start, ScamReport.created_at < day_end)
            .count()
        )
        u_count = (
            db.query(User)
            .filter(User.created_at >= day_start, User.created_at < day_end)
            .count()
        )

        detection_trends.append({"date": label, "detections": det_count})
        scam_trends.append({"date": label, "reports": rep_count})
        user_growth.append({"date": label, "new_users": u_count})

    # Report resolution stats
    total_reports = db.query(ScamReport).count()
    resolved = db.query(ScamReport).filter(ScamReport.status == "resolved").count()
    verified = db.query(ScamReport).filter(ScamReport.status == "verified").count()
    rejected = db.query(ScamReport).filter(ScamReport.status == "rejected").count()

    resolution_stats = {
        "total": total_reports,
        "resolved": resolved,
        "verified": verified,
        "rejected": rejected,
        "resolution_rate_percent": round((resolved / total_reports * 100), 1) if total_reports > 0 else 0.0,
    }

    # Category breakdown
    cat_counts = (
        db.query(ScamDetection.category, func.count(ScamDetection.id))
        .group_by(ScamDetection.category)
        .all()
    )
    category_breakdown = [
        {"category": cat or "general", "count": count} for cat, count in cat_counts
    ]

    return AdminAnalyticsResponse(
        scam_trends=scam_trends,
        detection_trends=detection_trends,
        user_growth=user_growth,
        report_resolution_stats=resolution_stats,
        category_breakdown=category_breakdown,
    )


# ---------------------------------------------------------
# User Management
# ---------------------------------------------------------
@router.get("/users")
def get_all_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """View, search, and filter all registered users with pagination."""
    query = db.query(User)

    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (User.email.ilike(s)) | (User.full_name.ilike(s)) | (User.customer_id.ilike(s))
        )
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "pages": pages,
        "items": [UserResponse.from_orm(u) for u in users]
    }


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """View full user profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.from_orm(user)


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    data: UserStatusUpdateRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Suspend or reactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot alter your own status")

    user.status = data.status
    user.updated_at = datetime.utcnow()
    _log_admin_action(db, admin.id, f"user_status_{data.status}", "user", user.id, {"new_status": data.status}, request)
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    data: UserRoleUpdateRequest,
    request: Request,
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Change a user's role (Superadmin only). Protects against unauthorized privilege escalation."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = data.role
    user.updated_at = datetime.utcnow()
    _log_admin_action(db, admin.id, f"role_changed_{data.role}", "user", user.id, {"new_role": data.role}, request)
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Delete a user account (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own administrator account")

    _log_admin_action(db, admin.id, "user_deleted", "user", user.id, {"email": user.email}, request)
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted successfully."}


# ---------------------------------------------------------
# Report Management
# ---------------------------------------------------------
@router.get("/reports")
def get_all_admin_reports(
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """View and filter all submitted scam reports with administrative oversight."""
    query = db.query(ScamReport)
    if status:
        query = query.filter(ScamReport.status == status)
    if category:
        query = query.filter(ScamReport.category == category)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (ScamReport.title.ilike(s))
            | (ScamReport.description.ilike(s))
            | (ScamReport.suspicious_phone.ilike(s))
            | (ScamReport.suspicious_url.ilike(s))
        )

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    reports = query.order_by(ScamReport.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "pages": pages,
        "items": [ReportResponse.from_orm(r) for r in reports]
    }


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_admin_report_detail(
    report_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve full details for a scam report."""
    report = db.query(ScamReport).filter(ScamReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportResponse.from_orm(report)


@router.patch("/reports/{report_id}/status", response_model=ReportResponse)
def update_report_status(
    report_id: int,
    data: ReportStatusUpdateRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Review and update report status (verify, resolve, reject) and record admin notes."""
    report = db.query(ScamReport).filter(ScamReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report.status = data.status
    if data.admin_notes:
        report.admin_notes = data.admin_notes
    report.assigned_reviewer_id = admin.id
    report.updated_at = datetime.utcnow()

    _log_admin_action(db, admin.id, f"report_status_{data.status}", "report", report.id, {"status": data.status}, request)
    db.commit()
    db.refresh(report)
    return ReportResponse.from_orm(report)


@router.delete("/reports/{report_id}")
def delete_admin_report(
    report_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a report."""
    report = db.query(ScamReport).filter(ScamReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    _log_admin_action(db, admin.id, "report_deleted", "report", report.id, {"title": report.title}, request)
    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully."}


# ---------------------------------------------------------
# Detection Monitoring
# ---------------------------------------------------------
@router.get("/detections")
def get_admin_detections(
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Audit all detection events across users and public visitors."""
    query = db.query(ScamDetection)
    if category:
        query = query.filter(ScamDetection.category == category)
    if risk_level:
        query = query.filter(ScamDetection.risk_level == risk_level)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (ScamDetection.query_target.ilike(s)) | (ScamDetection.verdict.ilike(s))
        )

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    detections = query.order_by(ScamDetection.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "pages": pages,
        "items": [DetectionResponse.from_orm(d) for d in detections]
    }


# ---------------------------------------------------------
# Activity Logs & System Telemetry
# ---------------------------------------------------------
@router.get("/activity-logs", response_model=PaginatedActivityLogs)
def get_activity_logs(
    page: int = 1,
    limit: int = 25,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Audit trail of administrative and security events."""
    query = db.query(ActivityLog)
    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    logs = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        admin_name = log.admin.full_name if log.admin else "System / Automated"
        items.append(ActivityLogResponse(
            id=log.id,
            admin_id=log.admin_id,
            admin_name=admin_name,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
        ))

    return PaginatedActivityLogs(total=total, page=page, pages=pages, items=items)


@router.get("/system/health", response_model=SystemHealthResponse)
def get_system_health(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Detailed health check for administrative diagnostics."""
    db_status = "operational"
    try:
        db.execute(func.now())
    except Exception:
        db_status = "degraded"

    return SystemHealthResponse(
        status="healthy" if db_status == "operational" else "degraded",
        database=db_status,
        timestamp=datetime.utcnow(),
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/system/statistics", response_model=SystemStatisticsResponse)
def get_system_statistics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """System runtime statistics."""
    uptime = time.time() - _SERVER_START_TIME
    total_records = (
        db.query(User).count()
        + db.query(ScamDetection).count()
        + db.query(ScamReport).count()
        + db.query(ActivityLog).count()
    )
    logs_count = db.query(ActivityLog).count()

    return SystemStatisticsResponse(
        uptime_seconds=round(uptime, 1),
        total_db_records=total_records,
        active_sessions=1,
        security_events_logged=logs_count,
    )


# ---------------------------------------------------------
# Real Estate Estate Governance Endpoints
# ---------------------------------------------------------
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.booking import SiteVisitBooking, BookingStatus
from app.models.property import Property, PropertyStatus, PropertyType
from app.schemas.inquiry import InquiryResponse
from app.schemas.booking import BookingResponse
from app.schemas.property import PropertyResponse, PropertyCreate, PropertyUpdate


@router.get("/realestate/overview")
def get_realestate_admin_overview(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Aggregated metrics for MNA Real Estate & Construction administration."""
    total_properties = db.query(Property).count()
    total_inquiries = db.query(Inquiry).count()
    new_inquiries = db.query(Inquiry).filter(Inquiry.status == InquiryStatus.new).count()
    total_bookings = db.query(SiteVisitBooking).count()
    pending_bookings = db.query(SiteVisitBooking).filter(SiteVisitBooking.status == BookingStatus.pending).count()
    total_users = db.query(User).count()

    recent_inquiries = (
        db.query(Inquiry)
        .order_by(Inquiry.created_at.desc())
        .limit(5)
        .all()
    )
    recent_bookings = (
        db.query(SiteVisitBooking)
        .order_by(SiteVisitBooking.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_properties": total_properties,
        "total_inquiries": total_inquiries,
        "new_inquiries": new_inquiries,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "total_users": total_users,
        "recent_inquiries": [InquiryResponse.model_validate(i) for i in recent_inquiries],
        "recent_bookings": [BookingResponse.model_validate(b) for b in recent_bookings],
    }


@router.get("/inquiries")
def get_all_inquiries(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve all lead inquiries with filtering and search."""
    query = db.query(Inquiry)
    if status:
        query = query.filter(Inquiry.status == status)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (Inquiry.name.ilike(s)) | (Inquiry.email.ilike(s)) | (Inquiry.message.ilike(s))
        )

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    items = query.order_by(Inquiry.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "pages": pages,
        "items": [InquiryResponse.model_validate(i) for i in items],
    }


@router.patch("/inquiries/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: int,
    status_update: Dict[str, Any],
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update lead status (new, contacted, closed) and internal admin notes."""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    new_status = status_update.get("status")
    if new_status and new_status in [s.value for s in InquiryStatus]:
        inquiry.status = InquiryStatus(new_status)
    if "admin_notes" in status_update:
        inquiry.admin_notes = status_update["admin_notes"]

    db.commit()
    db.refresh(inquiry)

    _log_admin_action(
        db, admin.id, f"UPDATE_INQUIRY_STATUS_{inquiry.status.value}",
        "inquiry", inquiry.id, {"status": inquiry.status.value}, request
    )
    return InquiryResponse.model_validate(inquiry)


@router.delete("/inquiries/{inquiry_id}")
def delete_inquiry(
    inquiry_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an inquiry record."""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    db.delete(inquiry)
    db.commit()

    _log_admin_action(
        db, admin.id, "DELETE_INQUIRY", "inquiry", inquiry_id, None, request
    )
    return {"message": "Inquiry successfully removed."}


@router.get("/bookings")
def get_all_bookings(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve all site visit appointments with filtering and search."""
    query = db.query(SiteVisitBooking)
    if status:
        query = query.filter(SiteVisitBooking.status == status)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (SiteVisitBooking.visitor_name.ilike(s))
            | (SiteVisitBooking.visitor_email.ilike(s))
            | (SiteVisitBooking.visitor_phone.ilike(s))
        )

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    items = (
        query.order_by(SiteVisitBooking.visit_date.desc(), SiteVisitBooking.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "pages": pages,
        "items": [BookingResponse.model_validate(b) for b in items],
    }


@router.patch("/bookings/{booking_id}/status")
def update_booking_status(
    booking_id: int,
    status_update: Dict[str, Any],
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update site visit booking status (pending, confirmed, completed, cancelled)."""
    booking = db.query(SiteVisitBooking).filter(SiteVisitBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    new_status = status_update.get("status")
    if new_status and new_status in [s.value for s in BookingStatus]:
        booking.status = BookingStatus(new_status)
    if "admin_notes" in status_update:
        booking.admin_notes = status_update["admin_notes"]

    db.commit()
    db.refresh(booking)

    _log_admin_action(
        db, admin.id, f"UPDATE_BOOKING_STATUS_{booking.status.value}",
        "booking", booking.id, {"status": booking.status.value}, request
    )
    return BookingResponse.model_validate(booking)


@router.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a booking record."""
    booking = db.query(SiteVisitBooking).filter(SiteVisitBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    db.delete(booking)
    db.commit()

    _log_admin_action(
        db, admin.id, "DELETE_BOOKING", "booking", booking_id, None, request
    )
    return {"message": "Booking successfully removed."}


@router.post("/properties", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    prop_in: PropertyCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new property listing."""
    existing = db.query(Property).filter(Property.slug == prop_in.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="A property with this slug already exists.")

    prop = Property(**prop_in.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)

    _log_admin_action(
        db, admin.id, "CREATE_PROPERTY", "property", prop.id, {"title": prop.title}, request
    )
    return PropertyResponse.model_validate(prop)


@router.patch("/properties/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    prop_update: PropertyUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update an existing property listing."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found.")

    update_data = prop_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prop, field, value)

    db.commit()
    db.refresh(prop)

    _log_admin_action(
        db, admin.id, "UPDATE_PROPERTY", "property", prop.id, {"updated_fields": list(update_data.keys())}, request
    )
    return PropertyResponse.model_validate(prop)


@router.delete("/properties/{property_id}")
def delete_property(
    property_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a property listing."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found.")

    db.delete(prop)
    db.commit()

    _log_admin_action(
        db, admin.id, "DELETE_PROPERTY", "property", property_id, {"title": prop.title}, request
    )
    return {"message": "Property deleted successfully."}
