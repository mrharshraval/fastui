"""FastUI Demos Domain Schemas & Presentation DTOs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DentalBusinessPresentation(BaseModel):
    name: str
    category: str | None = "Dental Clinic"
    phone: str | None = None
    email: str | None = None
    whatsapp: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    opening_hours: str | None = "Mon-Sat: 9:00 AM - 8:00 PM"
    rating: float | None = 4.9
    reviews_count: int | None = 120
    place_id: str | None = None
    website: str | None = None
    logo_url: str | None = None
    branches: list[dict[str, Any]] | None = None
    whatsapp_url: str | None = None
    social_links: dict[str, str] | None = None

    model_config = ConfigDict(from_attributes=True)


class DentalCustomization(BaseModel):
    hero_headline: str = "Where healthy smiles begin."
    hero_subheadline: str = "Comprehensive, gentle dental care tailored to your family's needs."
    hero_image_url: str = "/hero_dentist_v1.webp"
    doctor_name: str = "Dr. Sarah Jenkins"
    doctor_title: str = "Chief Dental Surgeon"
    doctor_bio: str = "Specializing in cosmetic dentistry and modern dental implants with a patient-first approach."
    doctor_photo_url: str = "/female_dentist_portrait_1.png"
    clinic_interior_url: str = "/hero_dentist_v1.webp"

    tagline: str | None = None
    about_text: str | None = None
    brand_colors: dict[str, str] | None = None
    doctors: list[dict[str, Any]] | None = None
    testimonials: list[dict[str, Any]] | None = None
    faqs: list[dict[str, Any]] | None = None
    facilities: list[str] | None = None
    certifications: list[str] | None = None
    insurance_providers: list[str] | None = None
    emergency_info: str | None = None
    booking_url: str | None = None
    branches: list[dict[str, Any]] | None = None
    reusable_images: dict[str, list[str]] | None = None
    whatsapp_url: str | None = None
    social_links: dict[str, str] | None = None

    model_config = ConfigDict(from_attributes=True)


class DentalDemoPresentation(BaseModel):
    """Sanitized, public presentation data model.

    Tokens and internal CRM fields (lead_id, score, owner_id) are intentionally excluded.
    """

    status: str = "active"
    template_id: str = "dental-default"
    business: DentalBusinessPresentation
    customization: DentalCustomization

    model_config = ConfigDict(from_attributes=True)


class DemoEventCreate(BaseModel):
    event_type: str = Field(
        ...,
        description="'demo_viewed', 'whatsapp_clicked', 'call_clicked', 'cta_clicked', 'page_viewed'",
    )
    session_id: str | None = None
    page_path: str | None = "/"
    referrer: str | None = None
    metadata_json: dict[str, Any] | None = None


class DemoCreateRequest(BaseModel):
    custom_overrides: dict[str, Any] | None = None


class DemoResponse(BaseModel):
    id: int
    business_id: int
    token: str
    demo_url: str
    status: str = "active"
    template_id: str = "dental-default"
    custom_overrides: dict[str, Any] | None = None
    view_count: int = 0
    last_viewed_at: datetime | str | None = None
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)
