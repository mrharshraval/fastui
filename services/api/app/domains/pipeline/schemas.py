"""FastUI Pipeline Domain Schemas & DTOs."""

from pydantic import BaseModel


class PipelineDealResponse(BaseModel):
    id: str
    business_name: str
    stage: str
    value: float | None = None
    probability: int | None = None
    priority: str | None = "medium"
    lead_id: int | None = None
    city: str | None = None
    category: str | None = None
