"""
FastUI Dynamic Locality Resolution Policy
=========================================
Orchestrates authoritative geographic providers, in-memory caching,
and validation into a strictly dynamic, production-grade locality resolver.
Explicitly rejects synthetic sector fallbacks, hardcoded registries, and disk persistence.
"""

import logging
from typing import List, Optional

from geo.caching import LocalityCache
from geo.models import Locality
from geo.providers.base import GeographicProvider
from geo.providers.nominatim import NominatimProvider
from geo.providers.overpass import OverpassProvider
from geo.validation import clean_city_name, parse_location_scope

logger = logging.getLogger("fastui.geo.resolver")


class DynamicLocalityResolver:
    """
    Production-grade dynamic locality resolver.
    Queries only authoritative geographic providers (OpenStreetMap Overpass and Nominatim),
    validates spatial containment, and caches results transiently in memory.
    """

    def __init__(
        self,
        providers: Optional[List[GeographicProvider]] = None,
        cache: Optional[LocalityCache] = None,
    ) -> None:
        self.providers: List[GeographicProvider] = (
            providers
            if providers is not None
            else [OverpassProvider(), NominatimProvider()]
        )
        self.cache: LocalityCache = cache if cache is not None else LocalityCache()

    async def resolve_entities(self, location: str) -> List[Locality]:
        """
        Resolves a location string into verified, typed Locality entities.
        Queries authoritative providers dynamically. Never fabricates data.
        """
        scope = parse_location_scope(location)
        if not scope.city:
            return []

        cache_key = clean_city_name(scope.city)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Locality cache hit for '{cache_key}': {len(cached)} areas")
            return cached

        discovered_entities: List[Locality] = []
        seen_names: set[str] = set()

        # Query authoritative providers sequentially until sufficient entities are found
        for provider in self.providers:
            try:
                provider_results = await provider.fetch_localities(scope)
                for loc in provider_results:
                    loc_key = loc.name.lower()
                    if loc_key not in seen_names:
                        seen_names.add(loc_key)
                        discovered_entities.append(loc)

                if len(discovered_entities) >= 15:
                    break
            except Exception as e:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed for '{location}': {e}",
                    exc_info=True,
                )
                continue

        if discovered_entities:
            self.cache.set(cache_key, discovered_entities)
            logger.info(
                f"Resolved {len(discovered_entities)} authoritative geographic localities for '{location}'"
            )
            return discovered_entities

        logger.info(f"No authoritative localities found for '{location}'.")
        return []

    async def resolve(self, location: str) -> List[str]:
        """
        Public API returning list of verified locality names.
        If no distinct micro-localities exist, returns an empty list.
        """
        entities = await self.resolve_entities(location)
        return [e.name for e in entities]

    async def aclose(self) -> None:
        """Deterministically closes all provider HTTP clients."""
        for provider in self.providers:
            try:
                await provider.aclose()
            except Exception as e:
                logger.debug(f"Error closing provider '{provider.provider_name}': {e}")

    async def __aenter__(self) -> "DynamicLocalityResolver":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
