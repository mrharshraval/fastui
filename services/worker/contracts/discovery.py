"""
FastUI Worker Discovery Contracts
=================================
Pydantic schemas and typed Redis messages for lead discovery.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DiscoverySearchParams(BaseModel):
    """Normalized search query parameters passed to source adapters."""

    target_audience: str = Field(..., description="Target business category, e.g. 'Dentist'")
    location: str = Field(
        ..., description="Target geographical location, e.g. 'Ahmedabad, Gujarat, India'"
    )
    limit: Optional[int] = Field(default=None, description="Optional max leads; None for uncapped")
    batch_size: Optional[int] = Field(default=None, description="Bounded batch chunk size")
    query_variations: Optional[List[str]] = Field(
        default=None, description="Optional query variations to broaden coverage"
    )
    source_preferences: Optional[List[str]] = Field(
        default=None, description="Enabled sources in order of preference"
    )
    cursor: Optional[str] = Field(default=None, description="Optional pagination/resumption cursor")


class DiscoveredLead(BaseModel):
    """A single business lead returned by a scraping source adapter."""

    name: str = Field(..., min_length=1, description="Clean human-readable display name")
    raw_name: Optional[str] = Field(default=None, description="Exact untouched name from scraper")
    normalized_name: Optional[str] = Field(
        default=None, description="Canonical search/matching key"
    )
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    has_whatsapp: bool = False
    whatsapp: Optional[str] = None
    source_platform: str = Field(default="google_maps")
    source_place_id: Optional[str] = Field(
        default=None, description="Unique source identifier (e.g. Google Place ID)"
    )
    source_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    google_maps_url: Optional[str] = None
    opening_hours: Optional[Union[Dict[str, Any], str]] = None
    business_status: Optional[str] = None


class DiscoverResponse(BaseModel):
    """Response envelope for discovery execution."""

    leads: List[DiscoveredLead]
    count: int
    exhausted: bool = Field(
        default=False, description="True if all enabled sources have no further results"
    )
    sources_exhausted: Optional[dict[str, bool]] = Field(
        default=None, description="Per-source exhaustion status"
    )
    peak_rss_mb: Optional[float] = Field(
        default=None, description="Peak memory RSS observed during execution"
    )
    next_cursor: Optional[str] = Field(
        default=None, description="Cursor for the next geographic area or batch"
    )
    current_locality: Optional[str] = Field(
        default=None, description="Active locality or sector queried"
    )
    localities_remaining: Optional[int] = Field(
        default=None, description="Count of remaining localities in this city"
    )


# ─────────────────────────────────────────────────────────────
# TYPED STREAM MESSAGES (Redis Streams)
# ─────────────────────────────────────────────────────────────


class DiscoveryTaskMessage(BaseModel):
    """Message payload consumed from fastui:discover:tasks."""

    message_id: str
    task_id: int
    job_id: int
    params: Optional[DiscoverySearchParams] = None


class DiscoveryResultMessage(BaseModel):
    """Message payload published to and consumed from fastui:discover:results."""

    message_id: str
    job_id: int
    task_id: int
    leads: List[DiscoveredLead] = Field(default_factory=list)
    exhausted: bool = False
    next_cursor: Optional[str] = None
    current_locality: Optional[str] = None
    localities_remaining: Optional[int] = None
    error: Optional[str] = None
