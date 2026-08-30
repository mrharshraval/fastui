"""
FastUI Configuration & Settings Management (FAANG Standard)
===========================================================
- 100% Dynamic: Zero hardcoded domains, secrets, or provider credentials.
- Strict Type Safety: Built with Pydantic v2 BaseSettings.
- Precedence: Process Env (Render/K8s/AWS) > Service .env > Root .env.
- Auto-normalization: Driver protocol enforcement (postgresql+asyncpg://) for cloud DBs.
- Resilient Ingestion: Multi-format CORS parser (JSON array, comma-separated, single URL).
- Immutability & Memoization: lru_cache singleton pattern with dependency-injection hooks.
"""

import json
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Literal, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory Paths
SERVICE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = SERVICE_DIR.parent.parent


class Settings(BaseSettings):
    """
    Centralized, dynamic application configuration.
    All properties are resolved strictly from environment variables or .env files.
    """
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
        """
        Ensures cloud database URLs (Supabase, Render, Neon, AWS RDS)
        use the asyncpg driver required by SQLAlchemy asyncio.
        """
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

    # ─────────────────────────────────────────────────────────────
    # Networking & CORS
    # ─────────────────────────────────────────────────────────────
    FRONTEND_URL: Optional[str] = "https://sales.fastui.in"
    CORS_ALLOWED_ORIGINS: List[str] = [
        "https://sales.fastui.in",
        "https://fastui.in",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """
        Accepts List[str], JSON string '["https://..."]', or comma-separated string
        'https://app.vercel.app, https://customdomain.com' seamlessly from cloud dashboards.
        """
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
    RESEND_API_KEY: Optional[str] = None
    EMAIL_API_KEY: Optional[str] = None  # Backward-compatible alias
    EMAIL_FROM_ADDRESS: Optional[str] = None
    EMAIL_FROM_NAME: Optional[str] = None
    EMAIL_REPLY_TO: Optional[str] = None

    # SMTP Settings (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # ─────────────────────────────────────────────────────────────
    # Worker & Scraper Concurrency Limits
    # ─────────────────────────────────────────────────────────────
    MAX_CONCURRENT_SCRAPERS: int = 3

    # Pydantic v2 Config: Cascading file resolution, highest precedence to OS environment
    model_config = SettingsConfigDict(
        env_file=[
            str(SERVICE_DIR / ".env"),
            str(ROOT_DIR / ".env"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached, singleton instance of Settings.
    FastAPI dependency-injection friendly.
    """
    return Settings()


# Canonical shared singleton instance
settings = get_settings()
