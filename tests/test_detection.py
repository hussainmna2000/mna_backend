from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_detect_phone():
    response = client.post(
        "/api/v1/detection/phone",
        json={"phone_number": "+18005550199", "context": "urgent payment required for lawsuit"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "phone"
    assert "risk_score" in data
    assert data["risk_score"] > 0
    assert "verdict" in data
    assert isinstance(data["threat_indicators"], list)


def test_detect_url():
    response = client.post(
        "/api/v1/detection/url",
        json={"url": "http://192.168.1.1/paypa1-secure-login.xyz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "url"
    assert data["risk_level"] in ["HIGH", "CRITICAL"]


def test_detect_message():
    response = client.post(
        "/api/v1/detection/message",
        json={"message_text": "Your account is suspended. Verify KYC immediately at link: bit.ly/test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "message"
    assert data["risk_score"] >= 40.0
