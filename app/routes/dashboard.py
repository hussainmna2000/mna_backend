from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.detection import ScamDetection
from app.models.report import ScamReport
from app.models.user import User
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    ThreatStatisticsResponse,
    StatisticsResponse,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Return live threat and protection overview metrics."""
    total_detections = db.query(ScamDetection).count()
    high_risk_count = (
        db.query(ScamDetection)
        .filter(ScamDetection.risk_level.in_(["HIGH", "CRITICAL"]))
        .count()
    )
    active_reports = (
        db.query(ScamReport)
        .filter(ScamReport.status.in_(["pending", "under_review", "verified"]))
        .count()
    )
    resolved_reports = (
        db.query(ScamReport)
        .filter(ScamReport.status == "resolved")
        .count()
    )

    # Average risk score across all scans
    avg_score_res = db.query(func.avg(ScamDetection.risk_score)).scalar()
    avg_score = round(float(avg_score_res), 1) if avg_score_res else 42.5

    return DashboardOverviewResponse(
        total_scams_detected=total_detections,
        high_risk_threats=high_risk_count,
        active_reports=active_reports,
        resolved_reports=resolved_reports,
        risk_index_score=avg_score,
        threat_trend="Moderate elevation across mobile and phishing vectors",
    )


@router.get("/threat-statistics", response_model=ThreatStatisticsResponse)
def get_threat_statistics(db: Session = Depends(get_db)):
    """Return distribution of threats by category, severity, and recent timeline."""
    # Category counts
    cat_counts = (
        db.query(ScamDetection.category, func.count(ScamDetection.id))
        .group_by(ScamDetection.category)
        .all()
    )
    by_category = {cat or "general": count for cat, count in cat_counts}

    # Ensure baseline categories exist
    for default_cat in ["phone", "message", "url", "email", "transaction"]:
        if default_cat not in by_category:
            by_category[default_cat] = 0

    # Risk level counts
    level_counts = (
        db.query(ScamDetection.risk_level, func.count(ScamDetection.id))
        .group_by(ScamDetection.risk_level)
        .all()
    )
    by_risk_level = {lvl: count for lvl, count in level_counts}
    for default_lvl in ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        if default_lvl not in by_risk_level:
            by_risk_level[default_lvl] = 0

    # Past 7 days timeline
    now = datetime.utcnow()
    timeline = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        count = (
            db.query(ScamDetection)
            .filter(ScamDetection.created_at >= day_start, ScamDetection.created_at < day_end)
            .count()
        )
        timeline.append({"date": day_start.strftime("%b %d"), "scans": count})

    common_types = [
        {"type": "Digital Arrest & Impersonation", "risk": "Critical", "frequency": "High"},
        {"type": "Fake KYC & Banking Suspension", "risk": "High", "frequency": "Very High"},
        {"type": "Crypto Guaranteed ROI Schemes", "risk": "High", "frequency": "Moderate"},
        {"type": "Courier Customs Package Scam", "risk": "High", "frequency": "Moderate"},
        {"type": "Remote Access APK Downloads", "risk": "Critical", "frequency": "High"},
    ]

    return ThreatStatisticsResponse(
        by_category=by_category,
        by_risk_level=by_risk_level,
        timeline_activity=timeline,
        common_scam_types=common_types,
    )


@router.get("/statistics", response_model=StatisticsResponse)
def get_general_statistics(db: Session = Depends(get_db)):
    """General aggregated counts."""
    users_count = db.query(User).count()
    detections_count = db.query(ScamDetection).count()
    reports_count = db.query(ScamReport).count()
    high_risk_count = (
        db.query(ScamDetection)
        .filter(ScamDetection.risk_level.in_(["HIGH", "CRITICAL"]))
        .count()
    )
    pct = round((high_risk_count / detections_count * 100), 1) if detections_count > 0 else 0.0

    return StatisticsResponse(
        total_users=users_count,
        total_detections=detections_count,
        total_reports=reports_count,
        high_risk_percentage=pct,
    )


@router.get("/recent-activity")
def get_recent_activity(db: Session = Depends(get_db)):
    """Public real-time threat feed with masked identifiers."""
    recent_scans = (
        db.query(ScamDetection)
        .order_by(ScamDetection.created_at.desc())
        .limit(10)
        .all()
    )
    result = []
    for s in recent_scans:
        # Mask query target to protect privacy
        target = s.query_target
        if s.category == "phone" and len(target) > 5:
            masked = target[:4] + "***" + target[-2:]
        elif s.category in ["url", "email"] and len(target) > 6:
            masked = target[:5] + "***" + target[-4:]
        else:
            masked = (target[:15] + "...") if len(target) > 15 else target

        result.append({
            "id": s.id,
            "category": s.category,
            "target": masked,
            "risk_level": s.risk_level,
            "risk_score": s.risk_score,
            "verdict": s.verdict,
            "time_ago": s.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        })
    return result
