import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "MNA Real Estate & Construction"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Database
    # Defaults to local SQLite for instant local dev & testing, switches to PostgreSQL in production
    DATABASE_URL: str = Field(
        default="sqlite:///./trustguard.db",
        env="DATABASE_URL"
    )

    # Security
    SECRET_KEY: str = Field(
        default="mna-realestate-production-super-secret-jwt-key-2026-secure",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://mna-realestate.vercel.app",
        "*"
    ]

    # Initial Admin Provisioning
    ADMIN_EMAIL: str = Field(default="admin@mna-realestate.com", env="ADMIN_EMAIL")
    ADMIN_PASSWORD: str = Field(default="Admin@123", env="ADMIN_PASSWORD")
    ADMIN_NAME: str = Field(default="MNA Principal Director", env="ADMIN_NAME")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
