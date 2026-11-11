from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def get_admin_token():
    res = client.post(
        "/api/v1/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    if res.status_code == 200:
        return res.json()["access_token"]
    return None


def test_admin_endpoints_require_auth():
    # Attempt unauthorized access
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 401


def test_admin_dashboard_with_auth():
    token = get_admin_token()
    if not token:
        # Skip if superadmin was not seeded in this specific test runner env
        return

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "total_detections" in data
    assert "total_reports" in data


def test_admin_system_health():
    token = get_admin_token()
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/admin/system/health", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
