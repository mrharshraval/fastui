"""
FastUI Dynamic Geographic Locality Resolution Engine
===================================================
Discovers real city localities, suburbs, neighbourhoods, and commercial zones
dynamically for any city worldwide using authoritative OpenStreetMap providers (Overpass and Nominatim).
Zero hardcoded registries, synthetic fallbacks, or persistent disk caches.
"""

from typing import List

from geo.caching import LocalityCache
from geo.models import Locality, LocalityType, LocationScope
from geo.providers.base import GeographicProvider
from geo.providers.nominatim import NominatimProvider
from geo.providers.overpass import OverpassProvider
from geo.resolver import DynamicLocalityResolver
from geo.validation import clean_city_name, clean_unicode_spaces, parse_location_scope

__all__ = [
    "DynamicLocalityResolver",
    "Locality",
    "LocalityType",
    "LocationScope",
    "LocalityCache",
    "GeographicProvider",
    "NominatimProvider",
    "OverpassProvider",
    "clean_unicode_spaces",
    "clean_city_name",
    "parse_location_scope",
    "resolve_city_localities",
]

_shared_cache = LocalityCache()


def get_default_resolver() -> DynamicLocalityResolver:
    """Returns a DynamicLocalityResolver instance backed by shared memory cache."""
    return DynamicLocalityResolver(cache=_shared_cache)


async def resolve_city_localities(location: str) -> List[str]:
    """
    Public Async API: Resolves a location string into an ordered list of verified geographic localities.
    Queries only authoritative providers dynamically.
    Ensures provider HTTP clients are cleanly closed in the caller's event loop.
    """
    resolver = get_default_resolver()
    try:
        return await resolver.resolve(location)
    finally:
        if hasattr(resolver, "aclose"):
            await resolver.aclose()
