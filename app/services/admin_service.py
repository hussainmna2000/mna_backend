"""Admin service: dashboard stats, analytics, activity logging."""
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.booking import SiteVisitBooking, BookingStatus
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.notification import Notification
from app.models.property import Property, PropertyStatus
from app.models.user import User, UserStatus


def get_dashboard_stats(db: Session) -> dict:
    """Compute real-time dashboard statistics from the database."""
    # Users
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.status == UserStatus.active).scalar()
    suspended_users = db.query(func.count(User.id)).filter(User.status == UserStatus.suspended).scalar()

    # Inquiries
    total_inquiries = db.query(func.count(Inquiry.id)).scalar()
    new_inquiries = db.query(func.count(Inquiry.id)).filter(Inquiry.status == InquiryStatus.new).scalar()
    closed_inquiries = db.query(func.count(Inquiry.id)).filter(Inquiry.status == InquiryStatus.closed).scalar()

    # Bookings
    total_bookings = db.query(func.count(SiteVisitBooking.id)).scalar()
    pending_bookings = db.query(func.count(SiteVisitBooking.id)).filter(
        SiteVisitBooking.status == BookingStatus.pending
    ).scalar()
    confirmed_bookings = db.query(func.count(SiteVisitBooking.id)).filter(
        SiteVisitBooking.status == BookingStatus.confirmed
    ).scalar()

    # Properties
    total_properties = db.query(func.count(Property.id)).scalar()
    prop_by_status_rows = (
        db.query(Property.status, func.count(Property.id))
        .group_by(Property.status)
        .all()
    )
    properties_by_status = {row[0].value: row[1] for row in prop_by_status_rows}

    # Recent activity (last 10)
    recent_logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "admin_id": log.admin_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in recent_logs
    ]

    return {
        "total_users": total_users,
        "active_users": active_users,
        "suspended_users": suspended_users,
        "total_inquiries": total_inquiries,
        "new_inquiries": new_inquiries,
        "closed_inquiries": closed_inquiries,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "total_properties": total_properties,
        "properties_by_status": properties_by_status,
        "recent_activity": recent_activity,
    }


def get_monthly_trend(db: Session, model, date_column, months: int = 12) -> list[dict]:
    """Return monthly counts for a given model/date_column over the past N months."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * months)
    rows = (
        db.query(
            func.to_char(date_column, "YYYY-MM").label("month"),
            func.count().label("count"),
        )
        .filter(date_column >= cutoff)
        .group_by("month")
        .order_by("month")
        .all()
    )
    return [{"month": r.month, "count": r.count} for r in rows]


def get_analytics_data(db: Session, months: int = 12) -> dict:
    """Aggregate analytics data for the admin dashboard."""
    return {
        "inquiries": get_monthly_trend(db, Inquiry, Inquiry.created_at, months),
        "bookings": get_monthly_trend(db, SiteVisitBooking, SiteVisitBooking.created_at, months),
        "users": get_monthly_trend(db, User, User.created_at, months),
    }


def log_activity(
    db: Session,
    action: str,
    entity_type: str,
    admin_id: int | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> ActivityLog:
    """Create an ActivityLog entry."""
    log = ActivityLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
