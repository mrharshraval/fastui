"""FastUI Modern API Application Assembly.

Configures application lifespan, database migrations, background notification loops,
CORS security, error handlers, and modular API routers.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

# Configure Windows Proactor event loop for subprocess/playwright stability
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from app.api.v1.router import v1_router
from app.config.settings import settings
from app.domains.engagement.service import ReminderNotificationService
from app.domains.models import Base
from app.infrastructure.database.migrations import run_safe_migrations
from app.infrastructure.database.session import engine, get_db_session
from app.infrastructure.logging.logger import setup_logging
from app.infrastructure.logging.middleware import RequestCorrelationMiddleware
from app.shared.exceptions import FastUIException

setup_logging(service_name="fastui-api")
logger = logging.getLogger("fastui.api")


async def _reminder_checker_loop() -> None:
    """Background loop running every 30 seconds to dispatch due reminder push alerts."""
    while True:
        try:
            await asyncio.sleep(30)
            async with get_db_session() as session:
                await ReminderNotificationService.process_due_reminders(session)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in reminder notification background loop: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and synchronize columns
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await run_safe_migrations(engine)
        logger.info("Database schema initialized and safe migrations synchronized successfully.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)

    # Launch background reminder push dispatcher
    reminder_task = asyncio.create_task(_reminder_checker_loop())
    try:
        yield
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="FastUI Sales API",
    version="1.0.0",
    description="Production-grade API for lead prospecting, sales pipeline, and exports.",
    lifespan=lifespan,
)

# Attach Request Correlation Middleware
app.add_middleware(RequestCorrelationMiddleware)

# CORS Configuration
configured_origins = [
    settings.FRONTEND_URL,
    *settings.CORS_ALLOWED_ORIGINS,
    "https://sales.fastui.in",
    "https://fastui.in",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
origins = list({o.strip() for o in configured_origins if o and isinstance(o, str) and o.strip()})

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/([a-zA-Z0-9_-]+\.)?fastui\.in$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    detail_msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
        content={
            "detail": exc.detail,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": detail_msg,
                "request_id": request_id,
            },
        },
    )


@app.exception_handler(FastUIException)
async def domain_exception_handler(request: Request, exc: FastUIException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception on [{request_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please contact support if the issue persists.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support if the issue persists.",
                "details": {"error_type": exc.__class__.__name__},
                "request_id": request_id,
            },
        },
    )


@app.get("/health", tags=["system"], summary="Service Health Check")
async def health_check():
    """Service and database health check endpoint."""
    db_status = "unknown"
    db_error = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "error"
        db_error = str(e)

    return {
        "status": "ok" if db_status == "connected" else "error",
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "error": db_error,
        },
    }


# Register versioned routers
app.include_router(v1_router)
