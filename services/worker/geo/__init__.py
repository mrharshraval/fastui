"""
FastUI Geo Package
==================
Authoritative geographic locality resolution.
"""

from geo.localities import (
    DynamicLocalityResolver,
    Locality,
    LocalityCache,
    LocalityType,
    LocationScope,
    clean_city_name,
    clean_unicode_spaces,
    parse_location_scope,
    resolve_city_localities,
)

__all__ = [
    "DynamicLocalityResolver",
    "Locality",
    "LocalityType",
    "LocationScope",
    "LocalityCache",
    "clean_unicode_spaces",
    "clean_city_name",
    "parse_location_scope",
    "resolve_city_localities",
]
