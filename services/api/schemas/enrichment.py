"""
FastUI Business Enrichment Schemas
==================================
Data models for asynchronous website enrichment, brand extraction,
dental clinical profiling, and technical website intelligence.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EnrichmentParams(BaseModel):
    """Input payload to trigger enrichment on a website."""
    website: str = Field(..., description="Target business website URL")
    business_name: Optional[str] = Field(default=None, description="Optional business name for context matching")


class EnrichedBrand(BaseModel):
    """Visual identity assets extracted from the website."""
    model_config = ConfigDict(extra="ignore")

    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    og_image_url: Optional[str] = None
    apple_touch_icon_url: Optional[str] = None
    primary_color: Optional[str] = None
    brand_name: Optional[str] = None
    meta_description: Optional[str] = None
    tagline: Optional[str] = None
    about_text: Optional[str] = None
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    logo_source: Optional[str] = None
    logo_type: Optional[str] = None
    logo_confidence: float = 0.0
    theme_color: Optional[str] = None
    meta_title: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None

    @property
    def name(self) -> Optional[str]:
        return self.brand_name


class EnrichedDoctor(BaseModel):
    """Practitioner profile discovered on the website."""
    model_config = ConfigDict(extra="ignore")

    name: str
    title: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    degrees: List[str] = Field(default_factory=list)
    specialties: List[str] = Field(default_factory=list)
    is_primary: bool = False
    credentials: Optional[str] = None
    confidence: float = 0.5
    source: str = "html"


class EnrichedTestimonial(BaseModel):
    """Authentic patient testimonial or review."""
    model_config = ConfigDict(extra="ignore")

    name: str
    quote: str
    rating: Optional[float] = 5.0
    date: Optional[str] = None
    source_url: Optional[str] = None


class EnrichedFAQ(BaseModel):
    """Frequently Asked Question and answer pair."""
    model_config = ConfigDict(extra="ignore")

    question: str
    answer: str
    category: Optional[str] = None


class EnrichedBranch(BaseModel):
    """Clinic branch or location profile."""
    model_config = ConfigDict(extra="ignore")

    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    map_url: Optional[str] = None


class TreatmentSignal(BaseModel):
    """Dental specialty signal with confidence score."""
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    category: Optional[str] = None
    detected: bool = False
    detected_terms: List[str] = Field(default_factory=list)
    keywords_matched: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Optional[str] = "body"

    def model_post_init(self, __context):
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
    emails: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    whatsapp_url: Optional[str] = None
    whatsapp: Optional[str] = None
    booking_url: Optional[str] = None
    booking_urls: List[str] = Field(default_factory=list)
    booking_provider: Optional[str] = None
    contact_page_url: Optional[str] = None
    address: Optional[str] = None
    social_links: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    def model_post_init(self, __context):
        import re
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

    cms: Optional[str] = None
    analytics: List[str] = Field(default_factory=list)
    widgets: List[str] = Field(default_factory=list)
    booking_provider: Optional[str] = None
    server: Optional[str] = None
    frameworks: List[str] = Field(default_factory=list)
    hosting: Optional[str] = None


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
    breakdown: Dict[str, Any] = Field(default_factory=dict)


class EnrichedBusinessProfile(BaseModel):
    """Aggregated enriched business profile."""
    model_config = ConfigDict(extra="ignore")

    website_url: str
    canonical_url: Optional[str] = None
    brand: EnrichedBrand = Field(default_factory=EnrichedBrand)
    tagline: Optional[str] = None
    about_text: Optional[str] = None
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    doctors: List[EnrichedDoctor] = Field(default_factory=list)
    primary_doctor: Optional[EnrichedDoctor] = None
    treatments: Dict[str, TreatmentSignal] = Field(default_factory=dict)
    contact: EnrichedContact = Field(default_factory=EnrichedContact)
    technology: EnrichedTechnology = Field(default_factory=EnrichedTechnology)
    quality: EnrichedQualityAudit = Field(default_factory=EnrichedQualityAudit)
    opening_hours: Optional[Dict[str, Any]] = None
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
    """Enrichment response envelope from the worker."""
    model_config = ConfigDict(extra="ignore")

    success: bool
    status: str = Field(default="completed")
    error: Optional[str] = None
    profile: Optional[EnrichedBusinessProfile] = None
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
    enriched_at: Optional[str] = None
    quality_score: Optional[int] = None
    brand: Optional[EnrichedBrand] = None
    primary_doctor: Optional[EnrichedDoctor] = None
    treatments_count: int = 0
    profile: Optional[EnrichedBusinessProfile] = None
