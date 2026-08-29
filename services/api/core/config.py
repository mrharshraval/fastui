from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=True)

class Settings(BaseSettings):
    """
    Central application settings loaded from environment variables with strong defaults.
    """
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastui"
    SQL_ECHO: bool = False
    
    JWT_SECRET_KEY: str = "super-secret-key-for-local-dev-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200 # 30 days
    
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://sales.fastui.in"
    ]
    
    # Email / Resend settings
    EMAIL_PROVIDER: str = "resend"
    RESEND_API_KEY: Optional[str] = None
    EMAIL_API_KEY: Optional[str] = None  # Backward compatibility
    EMAIL_FROM_ADDRESS: str = "team@fastui.in"
    EMAIL_FROM_NAME: str = "fastui"
    EMAIL_REPLY_TO: str = "team@fastui.in"
    
    # SMTP settings
    SMTP_HOST: str = "smtp.mailgun.org"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Scraper concurrency limit
    MAX_CONCURRENT_SCRAPERS: int = 3

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
