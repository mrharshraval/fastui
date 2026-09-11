"""FastUI Production Configuration & Settings Management.

Strict Type Safety with Pydantic v2 BaseSettings.
Precedence: OS Environment > Service .env > Root .env.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory Paths
SERVICE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = SERVICE_DIR.parent.parent


class Settings(BaseSettings):
    """Centralized, dynamic application configuration."""

    # ─────────────────────────────────────────────────────────────
    # Environment & Telemetry
    # ─────────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    SQL_ECHO: bool = False

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_test(self) -> bool:
        return self.ENVIRONMENT == "test"

    # ─────────────────────────────────────────────────────────────
    # Database Connection
    # ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./fastui_sales.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> str:
        """Ensures cloud database URLs use the asyncpg driver required by SQLAlchemy asyncio."""
        if not isinstance(v, str) or not v.strip():
            return "sqlite+aiosqlite:///./fastui_sales.db"
        url = v.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # ─────────────────────────────────────────────────────────────
    # Security & Authentication (JWT)
    # ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "super-secret-key-for-local-dev-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days default

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.is_production and (
            not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "super-secret-key-for-local-dev-only"
        ):
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY must be set to a secure, "
                "unique secret in production! Default development secret is forbidden."
            )
        return self

    # ─────────────────────────────────────────────────────────────
    # Networking & CORS
    # ─────────────────────────────────────────────────────────────
    FRONTEND_URL: str | None = "https://sales.fastui.in"
    DEMO_BASE_URL: str = "https://demo.fastui.in"
    CORS_ALLOWED_ORIGINS: list[str] = [
        "https://sales.fastui.in",
        "https://fastui.in",
        "https://demo.fastui.in",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Accepts List[str], JSON string '["https://..."]', or comma-separated string."""
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            # Comma-separated fallback
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []

    # ─────────────────────────────────────────────────────────────
    # Transactional Email (Resend & SMTP)
    # ─────────────────────────────────────────────────────────────
    EMAIL_PROVIDER: Literal["resend", "smtp", "mock"] = "mock"
    RESEND_API_KEY: str | None = None
    EMAIL_API_KEY: str | None = None  # Backward-compatible alias
    EMAIL_FROM_ADDRESS: str | None = None
    EMAIL_FROM_NAME: str | None = None
    EMAIL_REPLY_TO: str | None = None

    # SMTP Settings (Optional)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True

    # ─────────────────────────────────────────────────────────────
    # Worker & Scraper
    # ─────────────────────────────────────────────────────────────
    MAX_CONCURRENT_SCRAPERS: int = 3
    WORKER_URL: str | None = None
    WORKER_TOKEN: str | None = None
    GCP_SERVICE_ACCOUNT_KEY: str | None = None

    # ─────────────────────────────────────────────────────────────
    # Web Push (VAPID)
    # ─────────────────────────────────────────────────────────────
    VAPID_PUBLIC_KEY: str | None = None
    VAPID_PRIVATE_KEY: str | None = None
    VAPID_CLAIM_EMAIL: str = "notifications@fastui.in"

    # Pydantic v2 Config: Cascading file resolution
    model_config = SettingsConfigDict(
        env_file=[
            str(SERVICE_DIR / ".env"),
            str(ROOT_DIR / ".env"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached, singleton instance of Settings."""
    return Settings()


# Canonical shared singleton instance
settings = get_settings()
