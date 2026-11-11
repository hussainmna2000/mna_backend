from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_submit_report():
    response = client.post(
        "/api/v1/reports",
        json={
            "category": "phone",
            "title": "Automated Phone Fraud Test Report",
            "description": "Suspicious phone call asking for confidential security credentials.",
            "suspicious_phone": "+19998887777",
            "financial_loss": 0.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "phone"
    assert data["status"] == "pending"


def test_list_reports():
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
