from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Union, Any

# ─────────────────────────────────────────────────────────────
# BUSINESS & LEAD SCHEMAS
# ─────────────────────────────────────────────────────────────

class LeadResponse(BaseModel):
    id: int
    business_id: int
    owner_id: Optional[int] = None
    stage: str = "lead"
    priority: str = "medium"
    signal: str = "warm"
    score: int = 50
    source: str = "discover"
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

class BusinessResponse(BaseModel):
    id: int
    business_name: str
    category: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    has_whatsapp: bool = False
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    website_status: Union[str, object] = "unknown"
    
    # Prospect & Lead lifecycle attributes
    qualification_status: str = "unqualified"
    is_lead: bool = False
    lead_id: Optional[int] = None
    pipeline_stage: Optional[str] = None
    stage: Optional[str] = None
    priority: str = "medium"
    signal: str = "warm"
    score: int = 50
    
    # Contact tracking semantics
    last_outreach_at: Optional[Union[datetime, str]] = None
    last_contacted_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

class StageUpdateRequest(BaseModel):
    stage: str

class StageUpdateResponse(BaseModel):
    message: str
    business_id: int
    old_stage: str
    new_stage: str

class QualifyProspectRequest(BaseModel):
    qualification_status: str # "unqualified", "reviewing", "qualified", "disqualified"

class BulkAddToLeadsRequest(BaseModel):
    business_ids: List[int]

class BulkAddToLeadsResponse(BaseModel):
    message: str
    added_count: int
    business_ids: List[int]

class ContactResponse(BaseModel):
    id: int
    business_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_decision_maker: bool = False
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────────────────────────
# NOTE SCHEMAS
# ─────────────────────────────────────────────────────────────

class NoteCreateRequest(BaseModel):
    content: str
    contact_id: Optional[int] = None

class NoteResponse(BaseModel):
    id: int
    business_id: int
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    content: str
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────────────────────────
# OUTREACH SCHEMAS (What we attempted)
# ─────────────────────────────────────────────────────────────

class OutreachCreateRequest(BaseModel):
    channel: str # "call", "whatsapp", "email"
    recipient: str # phone number, email address
    status: Optional[str] = "initiated"
    subject: Optional[str] = None
    notes: Optional[str] = None
    contact_id: Optional[int] = None
    metadata_json: Optional[dict] = None

class OutreachResponse(BaseModel):
    id: int
    business_id: int
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    channel: str
    status: str
    recipient: str
    subject: Optional[str] = None
    notes: Optional[str] = None
    metadata_json: Optional[Any] = None
    attempted_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────────────────────────
# INTERACTION SCHEMAS (Actual two-way conversation / engagement)
# ─────────────────────────────────────────────────────────────

class InteractionCreateRequest(BaseModel):
    type: str # "call_conversation", "whatsapp_chat", "email_thread", "meeting", "demo"
    summary: Optional[str] = None
    outcome: Optional[str] = None
    sentiment: Optional[str] = "neutral" # "positive", "neutral", "negative"
    duration_seconds: Optional[int] = None
    outreach_id: Optional[int] = None
    contact_id: Optional[int] = None
    occurred_at: Optional[Union[datetime, str]] = None

class InteractionResponse(BaseModel):
    id: int
    business_id: int
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    outreach_id: Optional[int] = None
    type: str
    duration_seconds: Optional[int] = None
    summary: Optional[str] = None
    outcome: Optional[str] = None
    sentiment: Optional[str] = None
    occurred_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────────────────────────
# TASK SCHEMAS (Work that needs to be done)
# ─────────────────────────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "pending"
    due_date: Optional[Union[datetime, str]] = None
    contact_id: Optional[int] = None

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[Union[datetime, str]] = None

class TaskResponse(BaseModel):
    id: int
    business_id: int
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[Union[datetime, str]] = None
    completed_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────────────────────────
# REMINDER SCHEMAS (Time-based notification trigger)
# ─────────────────────────────────────────────────────────────

class ReminderCreateRequest(BaseModel):
    title: str
    due_at: Union[datetime, str]
    notes: Optional[str] = None
    contact_id: Optional[int] = None
    task_id: Optional[int] = None

class ReminderUpdateRequest(BaseModel):
    title: Optional[str] = None
    due_at: Optional[Union[datetime, str]] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ReminderResponse(BaseModel):
    id: int
    business_id: int
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    task_id: Optional[int] = None
    title: str
    notes: Optional[str] = None
    due_at: Union[datetime, str]
    status: str
    completed_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────────────────────────
# ACTIVITY SCHEMAS (Immutable timeline audit stream)
# ─────────────────────────────────────────────────────────────

class ActivityCreateRequest(BaseModel):
    type: str
    channel: Optional[str] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None
    contact_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class ActivityResponse(BaseModel):
    id: int
    business_id: int
    user_id: Optional[int] = None
    contact_id: Optional[int] = None
    type: Union[str, object]
    channel: Optional[str] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)
