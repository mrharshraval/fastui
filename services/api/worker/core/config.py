"""
FastUI Worker Configuration & Settings Management (FAANG Standard)
==================================================================
Strictly typed, centralized settings for the FastUI Background Worker daemon.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WORKER_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = WORKER_DIR.parent.parent


class WorkerSettings(BaseSettings):
    """
    Dedicated settings for the autonomous scraper and background processing worker.
    """
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./fastui_sales.db"

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

    # Concurrency & Polling
    MAX_CONCURRENT_SCRAPERS: int = 3
    JOB_POLL_INTERVAL_SECONDS: float = 2.0
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT_MS: int = 30000

    SQL_ECHO: bool = False

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


worker_settings = get_worker_settings()
settings = worker_settings
