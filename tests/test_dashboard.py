from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_overview():
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_scams_detected" in data
    assert "high_risk_threats" in data
    assert "risk_index_score" in data


def test_threat_statistics():
    response = client.get("/api/v1/dashboard/threat-statistics")
    assert response.status_code == 200
    data = response.json()
    assert "by_category" in data
    assert "by_risk_level" in data
    assert "timeline_activity" in data


def test_recent_activity():
    response = client.get("/api/v1/dashboard/recent-activity")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
