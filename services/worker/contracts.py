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
    limit: int = Field(default=50, ge=1, le=1000, description="Max leads to return in this batch/call")
    batch_size: int = Field(default=50, ge=1, le=100, description="Bounded batch chunk size")
    query_variations: Optional[List[str]] = Field(default=None, description="Optional query variations to broaden coverage")
    source_preferences: Optional[List[str]] = Field(default=None, description="Enabled sources in order of preference")
    cursor: Optional[str] = Field(default=None, description="Optional pagination/resumption cursor")


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
    source_place_id: Optional[str] = Field(default=None, description="Unique source identifier (e.g. Google Place ID)")
    source_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None


class DiscoverResponse(BaseModel):
    """Response envelope for the POST /discover endpoint."""

    leads: List[DiscoveredLead]
    count: int
    exhausted: bool = Field(default=False, description="True if all enabled sources have no further results")
    sources_exhausted: Optional[dict[str, bool]] = Field(default=None, description="Per-source exhaustion status")
    peak_rss_mb: Optional[float] = Field(default=None, description="Peak memory RSS observed during execution")

