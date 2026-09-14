"""
FastUI Geo Data Models
======================
Typed, immutable models for geographic scopes and locality entities.
Zero external I/O or framework dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LocalityType(str, Enum):
    SUBURB = "suburb"
    NEIGHBOURHOOD = "neighbourhood"
    QUARTER = "quarter"
    CITY_BLOCK = "city_block"
    TOWN = "town"
    DISTRICT = "district"
    COMMERCIAL = "commercial"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Locality:
    """Immutable representation of an authoritative geographic locality."""

    name: str
    city: str
    locality_type: LocalityType = LocalityType.UNKNOWN
    country: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass(frozen=True, slots=True)
class LocationScope:
    """Parsed, normalized geographic search scope."""

    raw_location: str
    city: str
    state: Optional[str] = None
    country: Optional[str] = None
