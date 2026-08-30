"""
FastUI Worker Client
====================
Thin HTTP client for dispatching discovery jobs to the private Cloud Run Worker.

Authentication strategy:
- Cloud Run IAM (Production Render → Cloud Run):
  Uses a Google Cloud Service Account key (configured in GCP_SERVICE_ACCOUNT_KEY env var)
  or metadata server to generate a signed Google OIDC ID Token for audience=WORKER_URL.
- Local development:
  Calls WORKER_URL directly (e.g. http://localhost:8001 or http://worker:8001).
"""

import json
import logging
import os
from typing import List, Optional

import httpx

from core.config import settings
from schemas.discovery import DiscoveredLead, DiscoverySearchParams

logger = logging.getLogger(__name__)

# Generous timeout — a full Playwright scrape can take 60-90 seconds
_DISCOVER_TIMEOUT = httpx.Timeout(120.0, connect=10.0)

# GCP metadata server endpoint for fetching OIDC ID tokens (when running inside GCP)
_METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
)


async def _fetch_oidc_token(audience: str) -> Optional[str]:
    """
    Fetches a valid Google OIDC ID Token for the target Cloud Run service audience.

    Resolution order:
    1. GCP_SERVICE_ACCOUNT_KEY env var (Service Account JSON string or file path) — for Render.
    2. GOOGLE_APPLICATION_CREDENTIALS env var (standard GCP credentials file).
    3. GCP Metadata Server (if running inside Google Cloud).
    """
    # 1. Check for Service Account Key configured as env variable (Render JSON string or file path)
    sa_key_raw = settings.GCP_SERVICE_ACCOUNT_KEY or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_key_raw:
        try:
            import google.auth.transport.requests
            from google.oauth2 import service_account

            auth_request = google.auth.transport.requests.Request()

            # Handle JSON string vs file path
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
                logger.debug("Successfully generated Google OIDC ID Token via Service Account key.")
                return creds.token
        except Exception as e:
            logger.warning(f"Failed to generate OIDC token via Service Account credentials: {e}")

    # 2. Check GCP Metadata Server (fallback if running inside GCP)
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
    """
    HTTP client for the FastUI Discovery Worker service.

    Usage:
        leads = await WorkerClient.discover(params)
    """

    @staticmethod
    async def discover(params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """
        Sends a POST /discover request to the Cloud Run Worker and returns discovered leads.
        """
        worker_url = settings.WORKER_URL
        if not worker_url:
            raise ValueError(
                "WORKER_URL is not configured. Real scraper worker on Cloud Run is required. "
                "Please set WORKER_URL in your environment settings."
            )

        worker_url = worker_url.rstrip("/")
        endpoint = f"{worker_url}/discover"

        headers = {"Content-Type": "application/json"}

        # Generate Google OIDC token if calling a remote HTTPS Cloud Run URL
        if worker_url.startswith("https://"):
            oidc_token = await _fetch_oidc_token(audience=worker_url)
            if oidc_token:
                headers["Authorization"] = f"Bearer {oidc_token}"
                logger.debug("OIDC token attached to worker request.")
            else:
                logger.info(
                    "No OIDC token generated. If Cloud Run requires authentication, "
                    "set GCP_SERVICE_ACCOUNT_KEY in your environment."
                )

        payload = params.model_dump()

        logger.info(
            f"Dispatching discover request to worker: "
            f"audience='{params.target_audience}' location='{params.location}' limit={params.limit}"
        )

        try:
            async with httpx.AsyncClient(timeout=_DISCOVER_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()

            data = response.json()
            raw_leads = data.get("leads", [])
            leads = [DiscoveredLead.model_validate(lead) for lead in raw_leads]
            logger.info(f"Worker returned {len(leads)} leads.")
            return leads

        except httpx.TimeoutException:
            logger.error(f"Worker request timed out after {_DISCOVER_TIMEOUT.read}s.")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Worker returned HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Worker request failed: {e}", exc_info=True)
            raise
