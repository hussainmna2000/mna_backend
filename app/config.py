import json
import os
from typing import Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "MNA Real Estate & Construction"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database
    # Defaults to local SQLite for instant local dev & testing, switches to PostgreSQL in production
    DATABASE_URL: str = "sqlite:///./trustguard.db"

    # Security
    SECRET_KEY: str = "mna-realestate-production-super-secret-jwt-key-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - Handles any format: JSON array string, comma-separated URLs, single URL string, or wildcard
    CORS_ORIGINS: Any = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://mna-realestate.vercel.app",
        "https://mna-frontend-qrovsceff-hussainmna2000-8199.vercel.app",
        "*"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v or v == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except Exception:
                    pass
            items = [item.strip() for item in v.split(",") if item.strip()]
            return items if items else ["*"]
        elif isinstance(v, (list, tuple)):
            return [str(item) for item in v]
        return ["*"]

    # Initial Admin Provisioning
    ADMIN_EMAIL: str = "admin@mna-realestate.com"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_NAME: str = "MNA Principal Director"


settings = Settings()
