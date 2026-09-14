"""
FastUI Geo Providers Package
============================
Authoritative geographic locality providers.
"""

from geo.providers.base import GeographicProvider
from geo.providers.nominatim import NominatimProvider
from geo.providers.overpass import OverpassProvider

__all__ = [
    "GeographicProvider",
    "NominatimProvider",
    "OverpassProvider",
]
