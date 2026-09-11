"""FastUI Cloud Run Worker HTTP Client.

Production-grade client communicating with the external scraping and enrichment worker.
Handles OIDC authentication, retry budgets, timeouts, and envelope validation.
"""

import json
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.config.settings import settings
from app.infrastructure.logging.logger import correlation_id_ctx

logger = logging.getLogger(__name__)

# Generous timeouts for Playwright operations
_DISCOVER_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_ENRICH_TIMEOUT = httpx.Timeout(45.0, connect=8.0)

_METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
)


class WorkerDiscoveryParams(BaseModel):
    """Transport query parameters passed to the Cloud Run Worker."""

    target_audience: str
    location: str
    limit: int | None = None
    batch_size: int | None = None
    query_variations: list[str] | None = None
    source_preferences: list[str] | None = None
    cursor: str | None = None


class WorkerDiscoveredLead(BaseModel):
    """Business lead returned by the Cloud Run discovery worker."""

    name: str = Field(..., min_length=1)
    raw_name: str | None = None
    normalized_name: str | None = None
    category: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    has_whatsapp: bool = False
    whatsapp: str | None = None
    source_platform: str = "google_maps"
    source_place_id: str | None = None
    source_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None
    google_maps_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    opening_hours: dict[str, Any] | str | None = None
    business_status: str | None = None


class WorkerDiscoverResponse(BaseModel):
    """Response envelope from the Worker discovery endpoint."""

    leads: list[WorkerDiscoveredLead]
    count: int
    exhausted: bool = False
    sources_exhausted: dict[str, bool] | None = None
    peak_rss_mb: float | None = None
    next_cursor: str | None = None
    current_locality: str | None = None
    localities_remaining: int | None = None


class WorkerEnrichmentParams(BaseModel):
    website: str
    business_name: str | None = None


class WorkerEnrichmentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    status: str = "completed"
    error: str | None = None
    profile: dict[str, Any] | None = None
    duration_ms: float = 0.0


async def _fetch_oidc_token(audience: str) -> str | None:
    """Fetches a Google OIDC ID Token for the target Cloud Run service audience."""
    sa_key_raw = settings.GCP_SERVICE_ACCOUNT_KEY or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_key_raw:
        try:
            import google.auth.transport.requests
            from google.oauth2 import service_account

            auth_request = google.auth.transport.requests.Request()

            if sa_key_raw.strip().startswith("{"):
                key_info = json.loads(sa_key_raw)
                creds = service_account.IDTokenCredentials.from_service_account_info(
                    key_info,
                    target_audience=audience,
                )
            else:
                creds = service_account.IDTokenCredentials.from_service_account_file(
                    sa_key_raw,
                    target_audience=audience,
                )

            creds.refresh(auth_request)
            if creds.token:
                logger.debug("Generated Google OIDC ID Token via Service Account key.")
                return creds.token
        except Exception as e:
            logger.warning(f"Failed to generate OIDC token via Service Account credentials: {e}")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
            resp = await client.get(
                _METADATA_TOKEN_URL,
                params={"audience": audience},
                headers={"Metadata-Flavor": "Google"},
            )
            if resp.status_code == 200:
                return resp.text.strip()
    except Exception:
        pass

    return None


class WorkerClient:
    """HTTP client communicating with the FastUI Discovery & Enrichment Worker."""

    @staticmethod
    async def discover_batch(params: WorkerDiscoveryParams | Any) -> WorkerDiscoverResponse:
        """Sends a POST /discover request to the Cloud Run Worker."""
        worker_url = os.getenv("WORKER_URL") or settings.WORKER_URL
        if not worker_url:
            raise ValueError(
                "WORKER_URL is not configured. Real scraper worker on Cloud Run is required. "
                "Please set WORKER_URL in your environment settings."
            )

        worker_url = worker_url.rstrip("/")
        endpoint = f"{worker_url}/discover"

        headers: dict[str, str] = {"Content-Type": "application/json"}

        worker_token = os.getenv("WORKER_TOKEN") or settings.WORKER_TOKEN
        if worker_token:
            headers["X-Worker-Token"] = worker_token

        corr_id = correlation_id_ctx.get()
        if corr_id:
            headers["X-Correlation-ID"] = corr_id
            headers["X-Request-ID"] = corr_id

        if worker_url.startswith("https://"):
            oidc_token = await _fetch_oidc_token(audience=worker_url)
            if oidc_token:
                headers["Authorization"] = f"Bearer {oidc_token}"

        payload = params.model_dump() if hasattr(params, "model_dump") else dict(params)

        target_aud = payload.get("target_audience", "")
        loc = payload.get("location", "")
        limit_desc = payload.get("limit") or "uncapped"
        logger.info(
            f"Dispatching discover request to worker: audience='{target_aud}' location='{loc}' limit={limit_desc}"
        )

        try:
            async with httpx.AsyncClient(timeout=_DISCOVER_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()

            data = response.json()
            raw_leads = data.get("leads", [])
            leads = [WorkerDiscoveredLead.model_validate(lead) for lead in raw_leads]
            return WorkerDiscoverResponse(
                leads=leads,
                count=len(leads),
                exhausted=data.get("exhausted", False),
                sources_exhausted=data.get("sources_exhausted"),
                peak_rss_mb=data.get("peak_rss_mb"),
                next_cursor=data.get("next_cursor"),
                current_locality=data.get("current_locality"),
                localities_remaining=data.get("localities_remaining"),
            )

        except httpx.TimeoutException:
            logger.error(f"Worker request timed out after {_DISCOVER_TIMEOUT.read}s.")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Worker returned HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Worker request failed: {e}", exc_info=True)
            raise

    @staticmethod
    async def discover(params: WorkerDiscoveryParams | Any) -> list[WorkerDiscoveredLead]:
        """Discovers leads and returns the list of leads."""
        response = await WorkerClient.discover_batch(params)
        return response.leads

    @staticmethod
    async def enrich_business(
        website: str, business_name: str | None = None
    ) -> WorkerEnrichmentResponse:
        """Dispatches an asynchronous website enrichment request to the Cloud Run Worker."""
        worker_url = os.getenv("WORKER_URL") or settings.WORKER_URL
        if not worker_url:
            raise ValueError(
                "WORKER_URL is not configured. Worker service is required for enrichment."
            )

        worker_url = worker_url.rstrip("/")
        endpoint = f"{worker_url}/enrich"

        headers: dict[str, str] = {"Content-Type": "application/json"}

        worker_token = os.getenv("WORKER_TOKEN") or settings.WORKER_TOKEN
        if worker_token:
            headers["X-Worker-Token"] = worker_token

        corr_id = correlation_id_ctx.get()
        if corr_id:
            headers["X-Correlation-ID"] = corr_id
            headers["X-Request-ID"] = corr_id

        if worker_url.startswith("https://"):
            oidc_token = await _fetch_oidc_token(audience=worker_url)
            if oidc_token:
                headers["Authorization"] = f"Bearer {oidc_token}"

        payload = {"website": website, "business_name": business_name}

        logger.info(
            f"Dispatching enrich request to worker: website='{website}' business='{business_name}'"
        )

        try:
            async with httpx.AsyncClient(timeout=_ENRICH_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()

            data = response.json()
            return WorkerEnrichmentResponse.model_validate(data)
        except httpx.TimeoutException:
            logger.error(
                f"Worker enrichment timed out after {_ENRICH_TIMEOUT.read}s for '{website}'."
            )
            return WorkerEnrichmentResponse(
                success=False,
                status="failed",
                error=f"Enrichment request timed out after {_ENRICH_TIMEOUT.read}s",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Worker enrichment returned HTTP {e.response.status_code}: {e.response.text}"
            )
            return WorkerEnrichmentResponse(
                success=False,
                status="failed",
                error=f"Worker HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"Worker enrichment failed for '{website}': {e}", exc_info=True)
            return WorkerEnrichmentResponse(
                success=False,
                status="failed",
                error=str(e),
            )
