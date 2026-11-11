"""
Comprehensive integration tests for MNA Real Estate & Construction backend APIs.
Tests property listings, inquiries, bookings, admin operations, and authentication.
"""
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_public_properties_listing():
    """Verify that property catalog is accessible without authentication."""
    response = client.get("/api/v1/properties")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


def test_submit_contact_inquiry():
    """Verify that visitors can submit a property inquiry."""
    payload = {
        "name": "Arun Kumar",
        "email": "arun.kumar@gmail.com",
        "phone": "+91 9840123456",
        "interest": "3BHK Villa",
        "message": "Looking for private villa with north facing entrance.",
    }
    response = client.post("/api/v1/inquiries", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["status"] == "new"


def test_book_site_visit():
    """Verify that visitors can schedule a site walkthrough."""
    # First get a valid property id
    props_res = client.get("/api/v1/properties")
    property_id = props_res.json()["items"][0]["id"]

    payload = {
        "visitor_name": "Meenakshi Sundaram",
        "visitor_email": "meenakshi.s@outlook.com",
        "visitor_phone": "+91 9789012345",
        "property_id": property_id,
        "visit_date": "2026-09-15",
        "visit_time": "10:30 AM",
        "notes": "Weekend model house walkthrough.",
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["visitor_name"] == payload["visitor_name"]
    assert data["status"] == "pending"


def test_admin_realestate_suite():
    """Verify admin login and full governance over inquiries, bookings, and properties."""
    # 1. Admin Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mna-realestate.com", "password": "Admin@123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Real Estate Overview
    overview_res = client.get("/api/v1/admin/realestate/overview", headers=headers)
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert "total_properties" in overview
    assert "total_inquiries" in overview
    assert "total_bookings" in overview

    # 3. List Inquiries
    inq_res = client.get("/api/v1/admin/inquiries", headers=headers)
    assert inq_res.status_code == 200
    inquiries = inq_res.json()
    assert "items" in inquiries
    assert len(inquiries["items"]) >= 1
    first_inq_id = inquiries["items"][0]["id"]

    # 4. Update Inquiry Status
    patch_inq_res = client.patch(
        f"/api/v1/admin/inquiries/{first_inq_id}/status",
        headers=headers,
        json={"status": "contacted", "admin_notes": "Discussed floor plans via phone."},
    )
    assert patch_inq_res.status_code == 200
    assert patch_inq_res.json()["status"] == "contacted"

    # 5. List Bookings
    book_res = client.get("/api/v1/admin/bookings", headers=headers)
    assert book_res.status_code == 200
    bookings = book_res.json()
    assert "items" in bookings
    assert len(bookings["items"]) >= 1
    first_book_id = bookings["items"][0]["id"]

    # 6. Update Booking Status
    patch_book_res = client.patch(
        f"/api/v1/admin/bookings/{first_book_id}/status",
        headers=headers,
        json={"status": "confirmed", "admin_notes": "Senior architect assigned for walkthrough."},
    )
    assert patch_book_res.status_code == 200
    assert patch_book_res.json()["status"] == "confirmed"

    # 7. Create New Property Listing
    new_prop_payload = {
        "title": "MNA Lakeview Enclave",
        "slug": "mna-lakeview-enclave-test",
        "tagline": "Scenic Waterfront Residential Community",
        "type": "custom",
        "status": "upcoming",
        "location": "Padiyur Lakefront, Tirupur",
        "city": "Padiyur Ottapalayam",
        "price_starting": "₹92 Lakhs",
        "bedrooms": "4 BHK",
        "carpet_area": "3,100 sq.ft",
        "possession_date": "January 2027",
        "completion_percentage": 15,
        "hero_image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        "description": "Exclusive waterfront villa development.",
    }
    create_prop_res = client.post("/api/v1/admin/properties", headers=headers, json=new_prop_payload)
    assert create_prop_res.status_code == 201
    created_prop = create_prop_res.json()
    assert created_prop["title"] == new_prop_payload["title"]

    # 8. Update Property Listing
    patch_prop_res = client.patch(
        f"/api/v1/admin/properties/{created_prop['id']}",
        headers=headers,
        json={"completion_percentage": 20},
    )
    assert patch_prop_res.status_code == 200
    assert patch_prop_res.json()["completion_percentage"] == 20

    # 9. Clean up test property
    del_res = client.delete(f"/api/v1/admin/properties/{created_prop['id']}", headers=headers)
    assert del_res.status_code == 200

    # 10. System Health
    health_res = client.get("/api/v1/admin/system/health", headers=headers)
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

