"""
FastUI Worker Contracts
=======================
Data transfer objects for the discover HTTP endpoint.
These are the canonical request/response schemas for the API→Worker boundary.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


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
    """Response envelope for the POST /discover endpoint."""

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
# WEBSITE ENRICHMENT CONTRACTS
# ─────────────────────────────────────────────────────────────


class EnrichmentParams(BaseModel):
    """Parameters for on-demand official website enrichment."""

    website: str = Field(..., description="Target business official website URL")
    business_name: Optional[str] = Field(
        default=None, description="Known clinic name for disambiguation"
    )
    location: Optional[str] = Field(default=None, description="Known geographic context")
    max_pages: int = Field(default=4, ge=1, le=8, description="Maximum internal subpages to visit")


class EnrichedBrand(BaseModel):
    """Brand identity assets and metadata extracted from official website."""

    logo_url: Optional[str] = None
    logo_source: Optional[str] = Field(
        default=None,
        description="'json_ld', 'apple_touch_icon', 'favicon', 'header_img', 'og_image'",
    )
    logo_type: Optional[str] = Field(default=None, description="'svg', 'png', 'webp', 'jpg', 'ico'")
    logo_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    favicon_url: Optional[str] = None
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    about_text: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    theme_color: Optional[str] = None
    brand_colors: Dict[str, str] = Field(
        default_factory=dict, description="Extracted palette: primary, secondary, accent"
    )
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None

    @property
    def name(self) -> Optional[str]:
        return self.brand_name


class EnrichedDoctor(BaseModel):
    """Practitioner or physician candidate extracted from official website."""

    name: str
    title: Optional[str] = None
    credentials: Optional[str] = None
    specialties: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_primary: bool = False
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = "html"


class EnrichedTestimonial(BaseModel):
    """Patient review or testimonial quoted on the clinic website."""

    name: str
    quote: str
    rating: Optional[float] = 5.0
    date: Optional[str] = None
    source_url: Optional[str] = None


class EnrichedFAQ(BaseModel):
    """Frequently asked question item extracted from website."""

    question: str
    answer: str
    category: Optional[str] = None


class EnrichedBranch(BaseModel):
    """Physical branch or clinic location listed on website."""

    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    map_url: Optional[str] = None


class TreatmentSignal(BaseModel):
    """Semantic signal for a dental treatment or clinical specialty."""

    model_config = ConfigDict(extra="ignore")

    name: str
    category: Optional[str] = None
    detected: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Optional[str] = None
    keywords_matched: List[str] = Field(default_factory=list)
    detected_terms: List[str] = Field(default_factory=list)

    def model_post_init(self, __context):
        if not self.category and self.name:
            self.category = self.name
        elif not self.name and self.category:
            self.name = self.category

        if not self.detected_terms and self.keywords_matched:
            self.detected_terms = list(self.keywords_matched)
        elif not self.keywords_matched and self.detected_terms:
            self.keywords_matched = list(self.detected_terms)


class EnrichedContact(BaseModel):
    """Direct contact, booking, and conversion intelligence."""

    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    whatsapp: Optional[str] = None
    whatsapp_url: Optional[str] = None
    booking_urls: List[str] = Field(default_factory=list)
    booking_provider: Optional[str] = None
    contact_page_url: Optional[str] = None
    social_links: dict[str, str] = Field(default_factory=dict)


class EnrichedTechnology(BaseModel):
    """Non-invasive web technology and CMS indicators."""

    cms: Optional[str] = None
    frameworks: List[str] = Field(default_factory=list)
    analytics: List[str] = Field(default_factory=list)
    hosting: Optional[str] = None


class EnrichedQualityAudit(BaseModel):
    """Lightweight objective website quality evaluation."""

    score: int = Field(default=50, ge=0, le=100, description="Overall quality score (0-100)")
    has_ssl: bool = False
    has_mobile_viewport: bool = False
    has_meta_description: bool = False
    has_structured_data: bool = False
    has_social_presence: bool = False
    has_online_booking: bool = False
    has_whatsapp_cta: bool = False
    has_clear_contact: bool = False
    breakdown: dict[str, Any] = Field(default_factory=dict)


class EnrichedBusinessProfile(BaseModel):
    """Aggregated feature-rich profile derived from official website enrichment."""

    website_url: str
    canonical_url: Optional[str] = None
    brand: EnrichedBrand = Field(default_factory=EnrichedBrand)
    tagline: Optional[str] = None
    about_text: Optional[str] = None
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    doctors: List[EnrichedDoctor] = Field(default_factory=list)
    primary_doctor: Optional[EnrichedDoctor] = None
    treatments: dict[str, TreatmentSignal] = Field(default_factory=dict)
    contact: EnrichedContact = Field(default_factory=EnrichedContact)
    technology: EnrichedTechnology = Field(default_factory=EnrichedTechnology)
    quality: EnrichedQualityAudit = Field(default_factory=EnrichedQualityAudit)
    opening_hours: Optional[dict[str, Any]] = None
    testimonials: List[EnrichedTestimonial] = Field(default_factory=list)
    faqs: List[EnrichedFAQ] = Field(default_factory=list)
    facilities: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    insurance_info: Dict[str, Any] = Field(default_factory=dict)
    emergency_services: Optional[str] = None
    unique_selling_points: List[str] = Field(default_factory=list)
    branches: List[EnrichedBranch] = Field(default_factory=list)
    reusable_images: Dict[str, List[str]] = Field(default_factory=dict)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    pages_crawled: List[str] = Field(default_factory=list)
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EnrichmentResponse(BaseModel):
    """Response envelope for the POST /enrich endpoint."""

    success: bool
    status: str = Field(default="completed", description="'completed', 'partial', 'failed'")
    error: Optional[str] = None
    profile: Optional[EnrichedBusinessProfile] = None
    duration_ms: float = 0.0
