"""FastUI Lead Domain Schemas & DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeadResponse(BaseModel):
    id: int
    business_id: int
    owner_id: int | None = None
    stage: str = "lead"
    priority: str = "medium"
    signal: str = "warm"
    score: int = 50
    source: str = "discover"
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class LeadCreateRequest(BaseModel):
    business_id: int | None = None
    business_ids: list[int] | None = None


class BulkAddToLeadsRequest(BaseModel):
    business_ids: list[int]


class BulkAddToLeadsResponse(BaseModel):
    message: str
    added_count: int
    business_ids: list[int]


class StageUpdateRequest(BaseModel):
    stage: str


class StageUpdateResponse(BaseModel):
    message: str
    business_id: int
    old_stage: str
    new_stage: str


class BulkStageRequest(BaseModel):
    business_ids: list[int]
    stage: str


class BulkStageResponse(BaseModel):
    updated_count: int
    business_ids: list[int]
    stage: str
    message: str | None = None
    new_stage: str | None = None
