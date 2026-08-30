"""
FastUI Discovery Worker
=======================
Standalone FastAPI service exposing a single authenticated HTTP endpoint.
Deployed as a private Google Cloud Run service (IAM-authenticated, no public access).

Endpoints:
  GET  /health   — liveness probe
  POST /discover — runs MultiSource Playwright scraping and returns discovered leads
"""

import logging
import sys

# Ensure the worker root is on sys.path so all local modules resolve correctly
import os
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from contracts import DiscoverResponse, DiscoverySearchParams
from core.config import settings
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exc.__class__.__name__, "detail": str(exc)},
    )


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness probe for Cloud Run and load balancers."""
    return {"status": "ok", "service": "fastui-worker"}


@app.post("/discover", response_model=DiscoverResponse, tags=["discovery"])
async def discover(params: DiscoverySearchParams) -> DiscoverResponse:
    """
    Runs multi-source Playwright scraping and returns discovered business leads.
    Authentication is enforced at the Cloud Run IAM layer — this endpoint trusts
    any request that reaches it.
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
