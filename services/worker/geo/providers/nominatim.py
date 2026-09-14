"""
FastUI Nominatim Geographic Provider
====================================
Dynamic settlement resolution via OpenStreetMap Nominatim API.
Enforces non-blocking async requests, connection reuse, and 1 req/sec rate limiting.
"""

import asyncio
import logging
import time
from typing import List, Optional

import httpx

from geo.models import Locality, LocalityType, LocationScope
from geo.validation import clean_unicode_spaces, is_geographic_match, is_valid_locality_name

logger = logging.getLogger("fastui.geo.nominatim")

DEFAULT_USER_AGENT = "FastUI-DiscoveryWorker/2.0 (authoritative-geo; contact: ops@fastui.internal)"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT_SEC = 8.0


class NominatimProvider:
    """Authoritative Nominatim OSM locality provider with rate-limiting and connection pooling."""

    provider_name: str = "nominatim"

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        min_interval_sec: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._client = client
        self._owns_client = client is None
        self._client_loop: Optional[asyncio.AbstractEventLoop] = None
        self._min_interval_sec = min_interval_sec
        self._last_request_time: float = 0.0
        self._rate_lock: Optional[asyncio.Lock] = None
        self._rate_lock_loop: Optional[asyncio.AbstractEventLoop] = None
        self._user_agent = user_agent

    def _get_rate_lock(self) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._rate_lock is None or self._rate_lock_loop is not loop:
            self._rate_lock = asyncio.Lock()
            self._rate_lock_loop = loop
        return self._rate_lock

    async def _get_client(self) -> httpx.AsyncClient:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if (
            self._client is None
            or getattr(self._client, "is_closed", False) is True
            or (self._client_loop is not None and (self._client_loop is not loop or self._client_loop.is_closed()))
        ):
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT_SEC,
                headers={"User-Agent": self._user_agent},
            )
            self._owns_client = True
            self._client_loop = loop
        return self._client

    async def _throttle(self) -> None:
        """Enforces OSM Nominatim policy: at most 1 request per second."""
        async with self._get_rate_lock():
            elapsed = time.monotonic() - self._last_request_time
            wait_time = self._min_interval_sec - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request_time = time.monotonic()

    async def fetch_localities(self, scope: LocationScope) -> List[Locality]:
        """
        Paginates across settlement categories in Nominatim within the target scope.
        Validates every match against strict geographic bounds.
        """
        if not scope.city:
            return []

        location_scope_str = (
            f"{scope.city}, {scope.country}" if scope.country else scope.city
        )
        categories = [
            ("suburb", f"suburbs in {location_scope_str}", LocalityType.SUBURB),
            ("neighbourhood", f"neighbourhoods in {location_scope_str}", LocalityType.NEIGHBOURHOOD),
            ("quarter", f"quarters in {location_scope_str}", LocalityType.QUARTER),
        ]

        seen_names: set[str] = set()
        localities: List[Locality] = []
        client = await self._get_client()

        for _cat_name, query_phrase, loc_type in categories:
            for page in range(1, 3):  # Max 2 pages per category (up to 100 items)
                try:
                    await self._throttle()

                    params = {
                        "q": query_phrase,
                        "format": "json",
                        "limit": "50",
                        "addressdetails": "1",
                    }
                    if page > 1:
                        params["offset"] = str((page - 1) * 50)

                    resp = await client.get(NOMINATIM_BASE_URL, params=params)
                    if resp.status_code != 200:
                        logger.warning(
                            f"Nominatim responded with HTTP {resp.status_code} for '{query_phrase}'"
                        )
                        break

                    data = resp.json()
                    if not isinstance(data, list) or not data:
                        break

                    new_items = 0
                    for item in data:
                        display_name = item.get("display_name", "")
                        address = item.get("address", {}) or {}

                        # Strict geographic containment verification
                        if not is_geographic_match(
                            display_name=display_name,
                            address=address,
                            target_city=scope.city,
                            target_country=scope.country,
                        ):
                            continue

                        raw_name = item.get("name") or display_name.split(",")[0]
                        clean_name = clean_unicode_spaces(raw_name)

                        if not is_valid_locality_name(clean_name, scope.city):
                            continue

                        name_key = clean_name.lower()
                        if name_key in seen_names:
                            continue

                        seen_names.add(name_key)
                        new_items += 1

                        lat = float(item["lat"]) if "lat" in item else None
                        lon = float(item["lon"]) if "lon" in item else None

                        localities.append(
                            Locality(
                                name=clean_name,
                                city=scope.city,
                                locality_type=loc_type,
                                country=address.get("country") or scope.country,
                                state=address.get("state") or scope.state,
                                postal_code=address.get("postcode"),
                                latitude=lat,
                                longitude=lon,
                            )
                        )

                    # Stop iterating pages if this page brought no new unique areas
                    if new_items == 0:
                        break

                except asyncio.CancelledError:
                    raise
                except httpx.HTTPError as e:
                    logger.warning(f"Nominatim network error for '{query_phrase}': {e}")
                    break
                except Exception as e:
                    logger.warning(f"Unexpected error in Nominatim search: {e}", exc_info=True)
                    break

        logger.info(
            f"NominatimProvider resolved {len(localities)} localities for '{scope.city}'"
        )
        return localities

    async def aclose(self) -> None:
        """Closes the underlying HTTP client."""
        if self._owns_client and self._client and not getattr(self._client, "is_closed", False):
            try:
                await self._client.aclose()
            except Exception as e:
                logger.debug(f"Error closing Nominatim client: {e}")
            finally:
                self._client = None
                self._client_loop = None
