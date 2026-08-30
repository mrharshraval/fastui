import os
import sys
import asyncio
import logging

# Ensure Windows ProactorEventLoop is active for subprocess/playwright support
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
service_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, service_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fastui.api")

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import FastUIException
from core.middleware import RequestCorrelationMiddleware
from models.database import engine, Base
from core.database_migration import run_safe_migrations
from routes import auth, prospecting, exports, businesses, stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and synchronize columns
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await run_safe_migrations(engine)
        logger.info("Database schema initialized and all columns synchronized successfully.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    yield

app = FastAPI(
    title="FastUI Sales API",
    version="1.0.0",
    description="Production-grade API for lead prospecting, sales pipeline, and exports.",
    lifespan=lifespan
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
@app.exception_handler(FastUIException)
async def domain_exception_handler(request: Request, exc: FastUIException):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception on [{request_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support if the issue persists.",
                "details": {"error_type": exc.__class__.__name__},
                "request_id": request_id
            }
        }
    )

from sqlalchemy import text
from models.database import engine

@app.get("/health", tags=["system"])
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
            "error": db_error
        }
    }

# Register modular route controllers
app.include_router(auth.router)
app.include_router(prospecting.router)
app.include_router(exports.router)
app.include_router(businesses.router)
app.include_router(stats.router)
