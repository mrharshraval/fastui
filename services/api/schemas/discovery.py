"""
FastUI Discovery & Lead Prospecting Schemas
===========================================
Data transfer objects for lead discovery queries and extracted business leads.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DiscoverySearchParams(BaseModel):
    """Normalized search query parameters passed to the Cloud Run Worker."""
    target_audience: str = Field(..., description="Target business category, e.g. 'Dentist'")
    location: str = Field(..., description="Target geographical location, e.g. 'Ahmedabad, Gujarat, India'")
    limit: int = Field(default=50, ge=1, le=1000, description="Max leads to fetch in this batch")
    batch_size: int = Field(default=50, ge=1, le=100, description="Batch chunk size")
    query_variations: Optional[list[str]] = Field(default=None, description="Optional query variations")
    source_preferences: Optional[list[str]] = Field(default=None, description="Enabled sources in order")
    cursor: Optional[str] = Field(default=None, description="Pagination cursor")


class DiscoveredLead(BaseModel):
    """Business lead returned by the Cloud Run discovery worker."""
    name: str = Field(..., min_length=1, description="Clean human-readable display name")
    raw_name: Optional[str] = Field(default=None, description="Exact untouched name received from scraper")
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
    source_place_id: Optional[str] = Field(default=None, description="Unique source place ID")
    source_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None


class DiscoverResponse(BaseModel):
    """Response envelope from the Worker."""
    leads: list[DiscoveredLead]
    count: int
    exhausted: bool = Field(default=False)
    sources_exhausted: Optional[dict[str, bool]] = None
    peak_rss_mb: Optional[float] = None

