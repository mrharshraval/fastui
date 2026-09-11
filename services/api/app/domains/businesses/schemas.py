"""FastUI Business Domain Schemas & DTOs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BusinessResponse(BaseModel):
    """Canonical representation of a business entity with lead/pipeline enrichment."""

    id: int
    business_name: str
    category: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    has_whatsapp: bool = False
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    website_status: str | Any = "unknown"

    # Prospect & Lead lifecycle attributes
    qualification_status: str = "unqualified"
    is_lead: bool = False
    lead_id: int | None = None
    pipeline_stage: str | None = None
    stage: str | None = None
    priority: str = "medium"
    signal: str = "warm"
    score: int = 50

    # Location & Mapping attributes
    google_maps_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None

    # Contact tracking semantics
    last_outreach_at: datetime | str | None = None
    last_contacted_at: datetime | str | None = None
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class BusinessUpdateRequest(BaseModel):
    """Payload for updating business properties."""

    business_name: str | None = None
    category: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    qualification_status: str | None = None
    stage: str | None = None
    priority: str | None = None
    signal: str | None = None
    score: int | None = None


class BulkDeleteRequest(BaseModel):
    business_ids: list[int] = Field(..., min_length=1)


class BulkDeleteResponse(BaseModel):
    message: str
    deleted_count: int
    business_ids: list[int]


class ContactResponse(BaseModel):
    id: str
    name: str
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = "Contact"
    email: str | None = None
    phone: str | None = None
    business_id: int | None = None
    company_name: str | None = "Independent"
    is_decision_maker: bool = False
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
