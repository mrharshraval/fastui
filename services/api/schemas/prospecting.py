from pydantic import BaseModel, Field
from typing import Optional

class LocationSchema(BaseModel):
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None

class ProspectingQuery(BaseModel):
    business_type: str = Field(..., min_length=1, description="e.g. Dentist, Plumber, Bakery")
    location: LocationSchema
    website_status: str = Field(default="any")

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
    error_message: Optional[str] = None
