"""
FastUI Worker Configuration & Settings Management
=================================================
Strictly typed, centralized settings for the FastUI Cloud Run Worker.
All values are resolved from environment variables — zero hardcoded secrets.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    # Server
    # ─────────────────────────────────────────────────────────────
    PORT: int = 8001

    # ─────────────────────────────────────────────────────────────
    # Concurrency & Browser
    # ─────────────────────────────────────────────────────────────
    MAX_CONCURRENT_SCRAPERS: int = 3
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT_MS: int = 30000

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
