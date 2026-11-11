import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import app
import httpx


async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health
        h = await client.get("/health")
        print("Health Check:", h.status_code, h.json())
        assert h.status_code == 200

        # 2. Public Phone Detection
        det = await client.post(
            "/api/v1/detection/phone",
            json={"phone_number": "+18005550199", "context": "urgent money transfer"},
        )
        print("Detection Phone:", det.status_code, det.json()["verdict"])
        assert det.status_code == 200

        # 3. Public URL Detection
        url_det = await client.post(
            "/api/v1/detection/url",
            json={"url": "http://192.168.1.1/paypa1-login.click"},
        )
        print("Detection URL:", url_det.status_code, url_det.json()["risk_level"])
        assert url_det.status_code == 200

        # 4. Dashboard Overview
        dash = await client.get("/api/v1/dashboard/overview")
        print("Dashboard Overview:", dash.status_code, dash.json())
        assert dash.status_code == 200

        # 5. Threat Stats
        threat = await client.get("/api/v1/dashboard/threat-statistics")
        print("Threat Stats:", threat.status_code, len(threat.json()["common_scam_types"]), "common types")
        assert threat.status_code == 200

        # 6. Auth Login (Admin)
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@trustguard.ai", "password": "TrustGuardAdmin2026!"},
        )
        print("Admin Login:", login.status_code, "role:", login.json()["user"]["role"])
        assert login.status_code == 200
        admin_token = login.json()["access_token"]

        # 7. Admin Dashboard Protected
        headers = {"Authorization": f"Bearer {admin_token}"}
        admin_dash = await client.get("/api/v1/admin/dashboard", headers=headers)
        print("Admin Dashboard:", admin_dash.status_code, "users:", admin_dash.json()["total_users"])
        assert admin_dash.status_code == 200

        # 8. Admin Users list
        users = await client.get("/api/v1/admin/users", headers=headers)
        print("Admin Users:", users.status_code, "count:", users.json()["total"])
        assert users.status_code == 200

        # 9. Admin Reports list
        reports = await client.get("/api/v1/admin/reports", headers=headers)
        print("Admin Reports:", reports.status_code, "count:", reports.json()["total"])
        assert reports.status_code == 200

        # 10. Admin Detections list
        detections = await client.get("/api/v1/admin/detections", headers=headers)
        print("Admin Detections:", detections.status_code, "count:", detections.json()["total"])
        assert detections.status_code == 200

        # 11. Admin System Health
        health_stat = await client.get("/api/v1/admin/system/health", headers=headers)
        print("Admin System Health:", health_stat.status_code, health_stat.json()["status"])
        assert health_stat.status_code == 200

        print("\nALL 11 CORE API ENDPOINT TESTS PASSED WITH 100% SUCCESS!")


if __name__ == "__main__":
    asyncio.run(main())
