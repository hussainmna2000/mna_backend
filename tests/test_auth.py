import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_register_and_login_flow():
    email = "testuser_auto@trustguard.ai"
    password = "TestPassword2026!"

    # 1. Register
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
            "phone": "+1234567890",
        },
    )
    # 201 Created or 400 if already exists from prior run
    if reg_response.status_code == 201:
        data = reg_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == email

    # 2. Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # 3. Access Protected Route /auth/me
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_invalid_login():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@trustguard.ai", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
