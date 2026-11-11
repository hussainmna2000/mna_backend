# MNA Real Estate & Construction — Enterprise API

Production-ready backend API service for **MNA Real Estate & Construction** (Padiyur Ottapalayam, Tirupur, Tamil Nadu).

---

## Architecture & Technology Stack

* **Framework:** Python 3.13 / FastAPI (Asynchronous ASGI)
* **Server:** Uvicorn / Gunicorn
* **ORM & Database:** SQLAlchemy 2.0 with PostgreSQL (Production) and SQLite (Local Fallback)
* **Migrations:** Alembic
* **Data Validation:** Pydantic v2 & Pydantic-Settings
* **Authentication:** OAuth2 with JWT access tokens, refresh token rotation, and bcrypt password hashing
* **Rate Limiting:** SlowAPI token bucket rate limiter
* **Testing:** Pytest with Starlette TestClient

---

## Directory Structure

```
backend/
├── app/
│   ├── config.py              # Application settings & environment variables
│   ├── database.py            # SQLAlchemy database engine and session factory
│   ├── main.py                # FastAPI entry point & router registrations
│   ├── middleware/            # Rate limiting, CORS, & JWT authentication middleware
│   ├── models/                # SQLAlchemy database entities (User, Property, Inquiry, Booking, etc.)
│   ├── routes/                # Modular REST API endpoints (Properties, Inquiries, Bookings, Auth, Admin, etc.)
│   ├── schemas/               # Pydantic request/response validation schemas
│   └── utils/                 # Security, JWT tokens, password hashing, ID generators
├── migrations/                # Alembic database migrations
├── tests/                     # Integration and automated test suite
├── alembic.ini                # Alembic configuration
├── create_admin.py            # Standalone admin provisioning script
├── seed_data.py               # Database seeder (Properties, Admin, Client, Inquiries, Bookings)
├── render.yaml                # Production deployment configuration for Render
└── requirements.txt           # Python dependency requirements
```

---

## Getting Started

### 1. Environment Setup
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```bash
python seed_data.py
```
This initializes the database schema and creates:
* **Superadmin:** `admin@mna-realestate.com` / `Admin@123`
* **Client User:** `client@mna-realestate.com` / `Client@123`
* 4 pre-configured luxury properties (Villas, Plots, Duplexes, Apartments)
* Sample inquiries and site visit bookings

### 4. Run the API Server
```bash
uvicorn app.main:app --reload --port 8000
```

* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check Probe:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Run Automated Tests
```bash
pytest backend/tests/test_realestate.py -v
```

---

## Production Deployment (Render)
This repository includes a `render.yaml` blueprint with a managed PostgreSQL database and FastAPI web service configured for automated continuous deployment.
