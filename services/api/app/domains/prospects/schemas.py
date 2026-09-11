"""FastUI Prospects Domain Schemas & DTOs."""

from pydantic import BaseModel


class QualifyProspectRequest(BaseModel):
    qualification_status: str


class BulkQualifyRequest(BaseModel):
    business_ids: list[int]
    qualification_status: str


class BulkQualifyResponse(BaseModel):
    updated_count: int
    business_ids: list[int]
    status: str | None = None
