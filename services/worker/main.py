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

# On Windows, Playwright requires ProactorEventLoop for async subprocess support
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from contracts import DiscoverResponse, DiscoverySearchParams
from core.config import settings
from core.security import verify_worker_token
from sources.aggregator import MultiSourceDiscoveryAggregator

from core.logger import setup_worker_logging

setup_worker_logging(service_name="fastui-worker")
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

import uuid
from core.logger import correlation_id_ctx

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    corr_id = (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )
    token = correlation_id_ctx.set(corr_id)
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response
    finally:
        correlation_id_ctx.reset(token)


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


def _run_discovery_in_proactor(params: DiscoverySearchParams, headless: bool):
    """
    Executes the Playwright scraping pipeline inside a dedicated ProactorEventLoop thread.
    Guarantees 100% subprocess support on Windows regardless of uvicorn's event loop policy.
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        aggregator = MultiSourceDiscoveryAggregator(headless=headless)
        return loop.run_until_complete(aggregator.discover_with_meta(params))
    finally:
        loop.close()


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
        leads, exhausted, sources_exhausted, peak_rss = await asyncio.to_thread(
            _run_discovery_in_proactor,
            params,
            settings.HEADLESS_BROWSER,
        )
        logger.info(
            f"Discovery complete: {len(leads)} leads returned "
            f"(exhausted={exhausted}, peak_rss={peak_rss:.1f}MB)."
        )
        return DiscoverResponse(
            leads=leads,
            count=len(leads),
            exhausted=exhausted,
            sources_exhausted=sources_exhausted,
            peak_rss_mb=peak_rss,
        )
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
