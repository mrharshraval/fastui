"""FastUI Enrichment Domain Schemas.

Data models for asynchronous website enrichment, brand extraction,
dental clinical profiling, and technical website intelligence.
"""

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EnrichmentParams(BaseModel):
    """Input payload to trigger enrichment on a website."""

    website: str = Field(..., description="Target business website URL")
    business_name: str | None = Field(
        default=None, description="Optional business name for context matching"
    )


class EnrichedBrand(BaseModel):
    """Visual identity assets extracted from the website."""

    model_config = ConfigDict(extra="ignore")

    logo_url: str | None = None
    favicon_url: str | None = None
    og_image_url: str | None = None
    apple_touch_icon_url: str | None = None
    primary_color: str | None = None
    brand_name: str | None = None
    meta_description: str | None = None
    tagline: str | None = None
    about_text: str | None = None
    brand_colors: dict[str, str] = Field(default_factory=dict)
    logo_source: str | None = None
    logo_type: str | None = None
    logo_confidence: float = 0.0
    theme_color: str | None = None
    meta_title: str | None = None
    og_title: str | None = None
    og_description: str | None = None

    @property
    def name(self) -> str | None:
        return self.brand_name


class EnrichedDoctor(BaseModel):
    """Practitioner profile discovered on the website."""

    model_config = ConfigDict(extra="ignore")

    name: str
    title: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    degrees: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    is_primary: bool = False
    credentials: str | None = None
    confidence: float = 0.5
    source: str = "html"


class EnrichedTestimonial(BaseModel):
    """Authentic patient testimonial or review."""

    model_config = ConfigDict(extra="ignore")

    name: str
    quote: str
    rating: float | None = 5.0
    date: str | None = None
    source_url: str | None = None


class EnrichedFAQ(BaseModel):
    """Frequently Asked Question and answer pair."""

    model_config = ConfigDict(extra="ignore")

    question: str
    answer: str
    category: str | None = None


class EnrichedBranch(BaseModel):
    """Clinic branch or location profile."""

    model_config = ConfigDict(extra="ignore")

    name: str
    address: str | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    map_url: str | None = None


class TreatmentSignal(BaseModel):
    """Dental specialty signal with confidence score."""

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    category: str | None = None
    detected: bool = False
    detected_terms: list[str] = Field(default_factory=list)
    keywords_matched: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str | None = "body"

    def model_post_init(self, __context: Any) -> None:
        if not self.category and self.name:
            self.category = self.name
        elif not self.name and self.category:
            self.name = self.category

        if not self.detected_terms and self.keywords_matched:
            self.detected_terms = list(self.keywords_matched)
        elif not self.keywords_matched and self.detected_terms:
            self.keywords_matched = list(self.detected_terms)

        if self.source is None:
            self.source = "body"


class EnrichedContact(BaseModel):
    """Contact methods and conversion links found on the website."""

    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    whatsapp_url: str | None = None
    whatsapp: str | None = None
    booking_url: str | None = None
    booking_urls: list[str] = Field(default_factory=list)
    booking_provider: str | None = None
    contact_page_url: str | None = None
    address: str | None = None
    social_links: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    def model_post_init(self, __context: Any) -> None:
        if not self.phone_numbers and self.phones:
            self.phone_numbers = list(self.phones)
        elif not self.phones and self.phone_numbers:
            self.phones = list(self.phone_numbers)

        if not self.whatsapp_url and self.whatsapp:
            if self.whatsapp.startswith("http"):
                self.whatsapp_url = self.whatsapp
            else:
                digits = re.sub(r"\D", "", self.whatsapp)
                self.whatsapp_url = f"https://wa.me/{digits}" if digits else None
        elif not self.whatsapp and self.whatsapp_url:
            self.whatsapp = self.whatsapp_url

        if not self.booking_url and self.booking_urls:
            self.booking_url = self.booking_urls[0]
        elif not self.booking_urls and self.booking_url:
            self.booking_urls = [self.booking_url]


class EnrichedTechnology(BaseModel):
    """Website tech stack fingerprints."""

    model_config = ConfigDict(extra="ignore")

    cms: str | None = None
    analytics: list[str] = Field(default_factory=list)
    widgets: list[str] = Field(default_factory=list)
    booking_provider: str | None = None
    server: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    hosting: str | None = None


class EnrichedQualityAudit(BaseModel):
    """Objective website quality score (0-100) and indicators."""

    model_config = ConfigDict(extra="ignore")

    score: int = Field(default=50, ge=0, le=100)
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
    """Aggregated enriched business profile."""

    model_config = ConfigDict(extra="ignore")

    website_url: str
    canonical_url: str | None = None
    brand: EnrichedBrand = Field(default_factory=EnrichedBrand)
    tagline: str | None = None
    about_text: str | None = None
    brand_colors: dict[str, str] = Field(default_factory=dict)
    doctors: list[EnrichedDoctor] = Field(default_factory=list)
    primary_doctor: EnrichedDoctor | None = None
    treatments: dict[str, TreatmentSignal] = Field(default_factory=dict)
    contact: EnrichedContact = Field(default_factory=EnrichedContact)
    technology: EnrichedTechnology = Field(default_factory=EnrichedTechnology)
    quality: EnrichedQualityAudit = Field(default_factory=EnrichedQualityAudit)
    opening_hours: dict[str, Any] | None = None
    testimonials: list[EnrichedTestimonial] = Field(default_factory=list)
    faqs: list[EnrichedFAQ] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    insurance_info: dict[str, Any] = Field(default_factory=dict)
    emergency_services: str | None = None
    unique_selling_points: list[str] = Field(default_factory=list)
    branches: list[EnrichedBranch] = Field(default_factory=list)
    reusable_images: dict[str, list[str]] = Field(default_factory=dict)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
    pages_crawled: list[str] = Field(default_factory=list)
    extracted_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class EnrichmentResponse(BaseModel):
    """Enrichment response envelope from the worker."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    status: str = Field(default="completed")
    error: str | None = None
    profile: EnrichedBusinessProfile | None = None
    duration_ms: float = 0.0


class EnrichmentTriggerResponse(BaseModel):
    """API response acknowledging enrichment background job start."""

    business_id: int
    status: str = "queued"
    message: str


class BusinessEnrichmentStatusResponse(BaseModel):
    """API response for querying a business's current enrichment state."""

    business_id: int
    is_enriched: bool
    enriched_at: str | None = None
    quality_score: int | None = None
    brand: EnrichedBrand | None = None
    primary_doctor: EnrichedDoctor | None = None
    treatments_count: int = 0
    profile: EnrichedBusinessProfile | None = None
