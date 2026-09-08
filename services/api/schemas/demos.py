from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, Union, List

# ─────────────────────────────────────────────────────────────
# PUBLIC PRESENTATION SCHEMAS (Unauthenticated Public Demo View)
# ─────────────────────────────────────────────────────────────

class DentalBusinessPresentation(BaseModel):
    name: str
    category: Optional[str] = "Dental Clinic"
    phone: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    opening_hours: Optional[str] = "Mon-Sat: 9:00 AM - 8:00 PM"
    rating: Optional[float] = 4.9
    reviews_count: Optional[int] = 120
    place_id: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    branches: Optional[List[Dict[str, Any]]] = None
    whatsapp_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None

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

    # Enriched Personalized Fields (Safe defaults ensure zero breaking changes)
    tagline: Optional[str] = None
    about_text: Optional[str] = None
    brand_colors: Optional[Dict[str, str]] = None
    doctors: Optional[List[Dict[str, Any]]] = None
    testimonials: Optional[List[Dict[str, Any]]] = None
    faqs: Optional[List[Dict[str, Any]]] = None
    facilities: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    insurance_providers: Optional[List[str]] = None
    emergency_info: Optional[str] = None
    booking_url: Optional[str] = None
    branches: Optional[List[Dict[str, Any]]] = None
    reusable_images: Optional[Dict[str, List[str]]] = None
    whatsapp_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)


class DentalDemoPresentation(BaseModel):
    """
    Sanitized, public presentation data model.
    Note: 'token' is intentionally excluded from this payload for security.
    No internal CRM fields (lead_id, score, owner_id, notes) are exposed.
    """
    status: str = "active"
    template_id: str = "dental-default"
    business: DentalBusinessPresentation
    customization: DentalCustomization

    model_config = ConfigDict(from_attributes=True)


class DemoEventCreate(BaseModel):
    event_type: str = Field(..., description="'demo_viewed', 'whatsapp_clicked', 'call_clicked', 'cta_clicked', 'page_viewed'")
    session_id: Optional[str] = None
    page_path: Optional[str] = "/"
    referrer: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────
# SALES CRM DEMO MANAGEMENT SCHEMAS (Authenticated Sales UI)
# ─────────────────────────────────────────────────────────────

class DemoCreateRequest(BaseModel):
    custom_overrides: Optional[Dict[str, Any]] = None


class DemoResponse(BaseModel):
    id: int
    business_id: int
    token: str
    demo_url: str
    status: str = "active"
    template_id: str = "dental-default"
    custom_overrides: Optional[Dict[str, Any]] = None
    view_count: int = 0
    last_viewed_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)
