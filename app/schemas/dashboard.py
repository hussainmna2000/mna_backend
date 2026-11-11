from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    total_scams_detected: int
    high_risk_threats: int
    active_reports: int
    resolved_reports: int
    risk_index_score: float
    threat_trend: str


class ThreatStatisticsResponse(BaseModel):
    by_category: Dict[str, int]
    by_risk_level: Dict[str, int]
    timeline_activity: List[Dict[str, Any]]
    common_scam_types: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    total_users: int
    total_detections: int
    total_reports: int
    high_risk_percentage: float
