"""FastUI Engagement Domain Schemas & DTOs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NoteCreateRequest(BaseModel):
    content: str
    contact_id: int | None = None


class NoteResponse(BaseModel):
    id: int
    business_id: int
    contact_id: int | None = None
    user_id: int | None = None
    content: str
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskCreateRequest(BaseModel):
    title: str
    description: str | None = None
    priority: str | None = "medium"
    status: str | None = "pending"
    due_date: datetime | str | None = None
    contact_id: int | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: datetime | str | None = None


class TaskResponse(BaseModel):
    id: int
    business_id: int
    contact_id: int | None = None
    user_id: int | None = None
    title: str
    description: str | None = None
    priority: str
    status: str
    due_date: datetime | str | None = None
    completed_at: datetime | str | None = None
    created_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class ReminderCreateRequest(BaseModel):
    title: str
    due_at: datetime | str
    notes: str | None = None
    contact_id: int | None = None
    task_id: int | None = None


class ReminderUpdateRequest(BaseModel):
    title: str | None = None
    due_at: datetime | str | None = None
    notes: str | None = None
    status: str | None = None


class ReminderResponse(BaseModel):
    id: int
    business_id: int
    contact_id: int | None = None
    user_id: int | None = None
    task_id: int | None = None
    title: str
    notes: str | None = None
    due_at: datetime | str
    status: str
    business_name: str | None = None
    contact_name: str | None = None
    completed_at: datetime | str | None = None
    created_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class OutreachCreateRequest(BaseModel):
    channel: str
    recipient: str
    status: str | None = "initiated"
    subject: str | None = None
    notes: str | None = None
    contact_id: int | None = None
    metadata_json: dict | None = None


class OutreachResponse(BaseModel):
    id: int
    business_id: int
    contact_id: int | None = None
    user_id: int | None = None
    channel: str
    status: str
    recipient: str
    subject: str | None = None
    notes: str | None = None
    metadata_json: Any | None = None
    attempted_at: datetime | str | None = None
    created_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class InteractionCreateRequest(BaseModel):
    type: str
    summary: str | None = None
    outcome: str | None = None
    sentiment: str | None = "neutral"
    duration_seconds: int | None = None
    outreach_id: int | None = None
    contact_id: int | None = None
    occurred_at: datetime | str | None = None


class InteractionResponse(BaseModel):
    id: int
    business_id: int
    contact_id: int | None = None
    user_id: int | None = None
    outreach_id: int | None = None
    type: str
    duration_seconds: int | None = None
    summary: str | None = None
    outcome: str | None = None
    sentiment: str | None = None
    occurred_at: datetime | str | None = None
    created_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


class ActivityCreateRequest(BaseModel):
    type: str
    channel: str | None = None
    outcome: str | None = None
    notes: str | None = None
    contact_id: int | None = None
    entity_type: str | None = None
    entity_id: int | None = None


class ActivityResponse(BaseModel):
    id: int
    business_id: int
    user_id: int | None = None
    user_name: str | None = None
    contact_id: int | None = None
    type: str | Any
    channel: str | None = None
    outcome: str | None = None
    notes: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    created_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)


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
