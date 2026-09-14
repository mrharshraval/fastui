"""
FastUI Overpass Geographic Provider
===================================
Boundary-contained settlement resolution via the OpenStreetMap Overpass API.
Queries OSM administrative areas across multiple public mirrors with automatic failover.
"""

import asyncio
import logging
from typing import List, Optional, Tuple

import httpx

from geo.models import Locality, LocalityType, LocationScope
from geo.validation import clean_unicode_spaces, is_valid_locality_name

logger = logging.getLogger("fastui.geo.overpass")

OVERPASS_MIRRORS: Tuple[str, ...] = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

DEFAULT_USER_AGENT = "FastUI-DiscoveryWorker/2.0 (authoritative-geo; contact: ops@fastui.internal)"
REQUEST_TIMEOUT_SEC = 10.0

SETTLEMENT_TYPE_MAP = {
    "suburb": LocalityType.SUBURB,
    "neighbourhood": LocalityType.NEIGHBOURHOOD,
    "quarter": LocalityType.QUARTER,
    "city_block": LocalityType.CITY_BLOCK,
    "town": LocalityType.TOWN,
    "district": LocalityType.DISTRICT,
}


class OverpassProvider:
    """Authoritative Overpass API locality provider with mirror failover and connection reuse."""

    provider_name: str = "overpass"

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        mirrors: Tuple[str, ...] = OVERPASS_MIRRORS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._client = client
        self._owns_client = client is None
        self._client_loop: Optional[asyncio.AbstractEventLoop] = None
        self._mirrors = mirrors
        self._user_agent = user_agent

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

    def _build_overpass_query(self, city_name: str) -> str:
        escaped_city = city_name.replace('"', '\\"')
        return f"""[out:json][timeout:10];
area["name"="{escaped_city}"]->.city;
(
  node["place"~"^(suburb|neighbourhood|quarter|city_block|town)$"](area.city);
  way["place"~"^(suburb|neighbourhood|quarter|city_block|town)$"](area.city);
);
out tags center 100;
"""

    async def fetch_localities(self, scope: LocationScope) -> List[Locality]:
        """
        Executes a boundary-contained Overpass settlement query with mirror failover.
        """
        if not scope.city:
            return []

        ql_query = self._build_overpass_query(scope.city)
        client = await self._get_client()

        for mirror in self._mirrors:
            try:
                resp = await client.post(mirror, data={"data": ql_query})
                if resp.status_code != 200:
                    logger.debug(
                        f"Overpass mirror '{mirror}' returned HTTP {resp.status_code} for '{scope.city}'"
                    )
                    continue

                data = resp.json()
                elements = data.get("elements", [])
                if not elements:
                    continue

                seen_names: set[str] = set()
                localities: List[Locality] = []

                for el in elements:
                    tags = el.get("tags", {}) or {}
                    raw_name = tags.get("name")
                    if not raw_name:
                        continue

                    clean_name = clean_unicode_spaces(raw_name)
                    if not is_valid_locality_name(clean_name, scope.city):
                        continue

                    name_key = clean_name.lower()
                    if name_key in seen_names:
                        continue

                    seen_names.add(name_key)
                    place_tag = tags.get("place", "unknown")
                    loc_type = SETTLEMENT_TYPE_MAP.get(place_tag, LocalityType.UNKNOWN)

                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")

                    localities.append(
                        Locality(
                            name=clean_name,
                            city=scope.city,
                            locality_type=loc_type,
                            country=scope.country,
                            state=scope.state,
                            latitude=float(lat) if lat is not None else None,
                            longitude=float(lon) if lon is not None else None,
                        )
                    )

                if len(localities) >= 5:
                    logger.info(
                        f"OverpassProvider resolved {len(localities)} localities for '{scope.city}' via '{mirror}'"
                    )
                    return localities

            except asyncio.CancelledError:
                raise
            except httpx.HTTPError as e:
                logger.debug(f"Overpass mirror '{mirror}' failed for '{scope.city}': {e}")
                continue
            except Exception as e:
                logger.debug(f"Unexpected error querying Overpass mirror '{mirror}': {e}", exc_info=True)
                continue

        logger.info(f"OverpassProvider found no sufficient localities for '{scope.city}'")
        return []

    async def aclose(self) -> None:
        """Closes the underlying HTTP client."""
        if self._owns_client and self._client and not getattr(self._client, "is_closed", False):
            try:
                await self._client.aclose()
            except Exception as e:
                logger.debug(f"Error closing Overpass client: {e}")
            finally:
                self._client = None
                self._client_loop = None
