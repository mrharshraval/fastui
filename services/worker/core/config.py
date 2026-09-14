"""
FastUI Worker Configuration & Settings Management
=================================================
Strictly typed, centralized settings for the FastUI Cloud Run Worker.
All values are resolved from environment variables — zero hardcoded secrets.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WORKER_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKER_DIR.parent.parent


class WorkerSettings(BaseSettings):
    """
    Configuration for the standalone Playwright scraping worker.
    Deployed as a private Cloud Run service.
    """

    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ─────────────────────────────────────────────────────────────
    # Concurrency & Browser
    # ─────────────────────────────────────────────────────────────
    MAX_CONCURRENT_SCRAPERS: int = 3
    MAX_CONCURRENT_ENRICHMENT: int = 4
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT_MS: int = 30000
    MEMORY_SAFETY_LIMIT_MB: float = 2048.0

    # ─────────────────────────────────────────────────────────────
    # Orchestration & Persistence
    # ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_STREAM_MAXLEN: int = 10000
    BACKPRESSURE_MAX_PENDING_RESULTS: int = 200
    DATABASE_URL: str = "sqlite+aiosqlite:///./fastui_sales.db"
    DB_POOL_SIZE: int = 4
    DB_MAX_OVERFLOW: int = 2
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 900

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            return "sqlite+aiosqlite:///./fastui_sales.db"
        url = v.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=[
            str(WORKER_DIR / ".env"),
            str(ROOT_DIR / ".env"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache()
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()


settings = get_worker_settings()
