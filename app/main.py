import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.middleware.rate_limit import limiter
from app.routes import (
    health,
    auth,
    users,
    properties,
    inquiries,
    bookings,
    detection,
    reports,
    dashboard,
    notifications,
    admin,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# Initialize tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")
except Exception as e:
    logger.error(f"Database initialization warning: {e}")

app = FastAPI(
    title="MNA Real Estate & Construction — Enterprise API",
    description=(
        "Production-grade backend API for MNA Real Estate & Construction. "
        "Provides property catalog management, client portal authentication, "
        "lead/inquiry tracking, site visit reservations, and comprehensive admin controls."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health Check
app.include_router(health.router)

# API v1 Routers
API_V1_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(users.router, prefix=API_V1_PREFIX)
app.include_router(properties.router, prefix=API_V1_PREFIX)
app.include_router(inquiries.router, prefix=API_V1_PREFIX)
app.include_router(bookings.router, prefix=API_V1_PREFIX)
app.include_router(detection.router, prefix=API_V1_PREFIX)
app.include_router(reports.router, prefix=API_V1_PREFIX)
app.include_router(dashboard.router, prefix=API_V1_PREFIX)
app.include_router(notifications.router, prefix=API_V1_PREFIX)
app.include_router(admin.router, prefix=API_V1_PREFIX)
