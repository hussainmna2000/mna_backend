from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.user import UserResponse
from app.schemas.report import ReportResponse
from app.schemas.detection import DetectionResponse


class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    suspended_users: int
    total_reports: int
    pending_reports: int
    resolved_reports: int
    total_detections: int
    high_risk_detections: int
    category_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class AdminAnalyticsResponse(BaseModel):
    scam_trends: List[Dict[str, Any]]
    detection_trends: List[Dict[str, Any]]
    user_growth: List[Dict[str, Any]]
    report_resolution_stats: Dict[str, Any]
    category_breakdown: List[Dict[str, Any]]


class ActivityLogResponse(BaseModel):
    id: int
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedActivityLogs(BaseModel):
    total: int
    page: int
    pages: int
    items: List[ActivityLogResponse]


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    app_version: str
    environment: str


class SystemStatisticsResponse(BaseModel):
    uptime_seconds: float
    total_db_records: int
    active_sessions: int
    security_events_logged: int
