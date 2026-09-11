"""FastUI Prospecting Domain Schemas & DTOs."""

from pydantic import BaseModel, Field


class LocationSchema(BaseModel):
    country: str | None = None
    state: str | None = None
    city: str | None = None
    locality: str | None = None


class ProspectingQuery(BaseModel):
    business_type: str = Field(..., min_length=1, description="e.g. Dentist, Plumber, Bakery")
    location: LocationSchema
    website_status: str = Field(default="any")
    target_count: int = Field(
        default=1000, ge=1, le=5000, description="Target unique prospects to discover"
    )


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: int
    total_discovered: int
    total_processed: int
    new_leads: int
    existing_businesses: int
    duplicates: int
    skipped: int
    errors: int
    target_count: int | None = None
    remaining_count: int | None = None
    error_message: str | None = None


class JobUpdateRequest(BaseModel):
    status: str | None = None
