"""
FastUI Worker Contracts
=======================
Data transfer objects for the discover HTTP endpoint.
These are the canonical request/response schemas for the API→Worker boundary.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class DiscoverySearchParams(BaseModel):
    """Normalized search query parameters passed to source adapters."""

    target_audience: str = Field(..., description="Target business category, e.g. 'Dentist'")
    location: str = Field(..., description="Target geographical location, e.g. 'Ahmedabad, Gujarat, India'")
    limit: int = Field(default=20, ge=1, le=100, description="Max leads to return")


class DiscoveredLead(BaseModel):
    """A single business lead returned by a scraping source adapter."""

    name: str = Field(..., min_length=1, description="Clean human-readable display name")
    raw_name: Optional[str] = Field(default=None, description="Exact untouched name from scraper")
    normalized_name: Optional[str] = Field(default=None, description="Canonical search/matching key")
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    source_platform: str = Field(default="google_maps")
    source_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None


class DiscoverResponse(BaseModel):
    """Response envelope for the POST /discover endpoint."""

    leads: List[DiscoveredLead]
    count: int
