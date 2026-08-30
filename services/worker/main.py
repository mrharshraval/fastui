"""
FastUI Discovery Worker
=======================
Standalone FastAPI service exposing lead discovery endpoints.
Deployed as a private Google Cloud Run service with application-level token authentication.

Endpoints:
  GET  /health   — unauthenticated liveness probe
  POST /discover — authenticated MultiSource Playwright scraping pipeline (requires X-Worker-Token)
"""

import logging
import os
import sys

# Ensure the worker root is on sys.path so all local modules resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from contracts import DiscoverResponse, DiscoverySearchParams
from core.config import settings
from core.security import verify_worker_token
from sources.aggregator import MultiSourceDiscoveryAggregator

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [worker] %(name)s: %(message)s",
)
logger = logging.getLogger("fastui.worker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"FastUI Discovery Worker starting "
        f"(env={settings.ENVIRONMENT}, headless={settings.HEADLESS_BROWSER}, "
        f"concurrency={settings.MAX_CONCURRENT_SCRAPERS})"
    )
    yield
    logger.info("FastUI Discovery Worker shutting down.")


app = FastAPI(
    title="FastUI Discovery Worker",
    version="1.0.0",
    description="Private Cloud Run service — Playwright-based lead discovery.",
    lifespan=lifespan,
    # Disable docs in production to reduce attack surface
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Pass-through for standard HTTP exceptions like 401 Unauthorized."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exc.__class__.__name__, "detail": str(exc)},
    )


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Unauthenticated liveness probe for Cloud Run and health checks."""
    return {"status": "ok", "service": "fastui-worker"}


@app.post(
    "/discover",
    response_model=DiscoverResponse,
    tags=["discovery"],
    dependencies=[Depends(verify_worker_token)],
)
async def discover(params: DiscoverySearchParams) -> DiscoverResponse:
    """
    Runs multi-source Playwright scraping and returns discovered business leads.
    Requires a valid 'X-Worker-Token' authentication header.
    """
    logger.info(
        f"Received discover request: audience='{params.target_audience}' "
        f"location='{params.location}' limit={params.limit}"
    )

    try:
        aggregator = MultiSourceDiscoveryAggregator(headless=settings.HEADLESS_BROWSER)
        leads = await aggregator.discover(params)
        logger.info(f"Discovery complete: {len(leads)} leads returned.")
        return DiscoverResponse(leads=leads, count=len(leads))
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
