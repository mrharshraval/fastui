import secrets
from typing import List, Optional, Union
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from core.config import settings
from models.database import get_db
from models.schema import ProspectDemo, Business
from schemas.demos import DemoCreateRequest, DemoResponse
from schemas.enrichment import (
    BusinessEnrichmentStatusResponse,
    EnrichmentTriggerResponse,
)
from schemas.businesses import (
    BusinessResponse,
    BusinessUpdateRequest,
    BulkDeleteRequest,
    BulkDeleteResponse,
    PipelineDealResponse,
    StageUpdateRequest,
    StageUpdateResponse,
    QualifyProspectRequest,
    BulkAddToLeadsRequest,
    BulkAddToLeadsResponse,
    LeadCreateRequest,
    OutreachCreateRequest,
    OutreachResponse,
    InteractionCreateRequest,
    InteractionResponse,
    NoteCreateRequest,
    NoteResponse,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    ReminderCreateRequest,
    ReminderUpdateRequest,
    ReminderResponse,
    ActivityCreateRequest,
    ActivityResponse,
    ContactResponse,
    BulkQualifyRequest,
    BulkQualifyResponse,
    BulkStageRequest,
)
from schemas.auth import TokenData
from services.auth_service import get_current_user
from services.business_service import BusinessService
from services.enrichment_service import EnrichmentService

router = APIRouter(tags=["sales_domain"])

# ─────────────────────────────────────────────────────────────
# 1. PROSPECTS (Discovered businesses before entering pipeline)
# ─────────────────────────────────────────────────────────────

@router.get("/prospects", response_model=List[BusinessResponse])
async def list_prospects(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    qualification_status: Optional[str] = Query(None, description="Filter by qualification status (unqualified, reviewing, qualified, disqualified)"),
    search: Optional[str] = Query(None, description="Search across business name, category, and city"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, business_name, city, qualification_status)"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction (asc or desc)"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Returns a paginated list of prospects (businesses not yet added to active Leads).
    """
    return await BusinessService.get_prospects(
        session=session,
        skip=skip,
        limit=limit,
        qualification_status=qualification_status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.patch("/prospects", response_model=BulkQualifyResponse)
async def update_prospects(
    req: BulkQualifyRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Partially updates qualification status across a collection of prospects.
    """
    return await BusinessService.bulk_qualify_prospects(
        session=session,
        business_ids=req.business_ids,
        qualification_status=req.qualification_status,
        current_user=current_user
    )


# ─────────────────────────────────────────────────────────────
# 2. LEADS (Businesses in active sales pipeline)
# ─────────────────────────────────────────────────────────────

@router.post("/leads", response_model=Union[BusinessResponse, BulkAddToLeadsResponse], status_code=status.HTTP_201_CREATED)
async def create_leads(
    req: LeadCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Creates a Lead resource for an existing business (or multiple businesses),
    promoting it into the active sales pipeline.
    """
    if req.business_ids:
        return await BusinessService.bulk_add_to_leads(
            session=session,
            business_ids=req.business_ids,
            current_user=current_user
        )
    if req.business_id is not None:
        return await BusinessService.add_to_leads(
            session=session,
            business_id=req.business_id,
            current_user=current_user
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either business_id or business_ids must be provided"
    )

@router.get("/leads", response_model=List[BusinessResponse])
async def list_leads(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    stage: Optional[str] = Query(None, description="Filter by pipeline stage (e.g. Lead, Contacted, Won)"),
    search: Optional[str] = Query(None, description="Search across business name, category, and city"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, business_name, city, pipeline_stage)"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction (asc or desc)"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Returns a paginated list of leads with active sales pipeline records.
    """
    return await BusinessService.get_businesses(
        session=session,
        skip=skip,
        limit=limit,
        stage=stage,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/businesses", response_model=List[BusinessResponse])
async def list_businesses(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    is_lead: Optional[bool] = Query(None, description="Filter by whether record is an active pipeline lead"),
    stage: Optional[str] = Query(None, description="Filter by pipeline stage"),
    search: Optional[str] = Query(None, description="Search across business name, category, and city"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, business_name, city)"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction (asc or desc)"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Returns a paginated list of all company/business accounts (both leads and non-leads).
    """
    return await BusinessService.get_all_businesses(
        session=session,
        skip=skip,
        limit=limit,
        is_lead=is_lead,
        stage=stage,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieves details for a single business/lead.
    """
    return await BusinessService.get_business_by_id(session=session, business_id=business_id)

@router.patch("/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    update: BusinessUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Updates business and associated lead details in the database.
    """
    return await BusinessService.update_business(
        session=session,
        business_id=business_id,
        req=update,
        current_user=current_user
    )

@router.delete("/businesses/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Deletes a business/lead record from the database.
    """
    await BusinessService.delete_business(
        session=session,
        business_id=business_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete("/businesses", response_model=BulkDeleteResponse)
async def bulk_delete_businesses(
    req: BulkDeleteRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Bulk deletes multiple businesses/leads from the database.
    """
    return await BusinessService.bulk_delete_businesses(
        session=session,
        business_ids=req.business_ids,
        current_user=current_user
    )

@router.get("/pipeline", response_model=List[PipelineDealResponse])
async def get_pipeline(
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Returns pipeline deals formatted for the pipeline board view.
    """
    return await BusinessService.get_pipeline_deals(
        session=session,
        current_user=current_user
    )

@router.patch("/leads")
async def update_leads_stage(
    req: BulkStageRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Bulk updates the pipeline stage of multiple leads.
    """
    return await BusinessService.bulk_update_stage(
        session=session,
        business_ids=req.business_ids,
        stage=req.stage,
        current_user=current_user
    )


# ─────────────────────────────────────────────────────────────
# 3. OUTREACH (What we attempted)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/outreach", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
async def log_outreach(
    business_id: int,
    request: OutreachCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Logs an outbound outreach attempt (call dial, whatsapp click, email send),
    updates last_outreach_at on business, and emits an audit Activity.
    """
    outreach = await BusinessService.log_outreach(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user
    )
    return OutreachResponse(
        id=outreach.id,
        business_id=outreach.business_id,
        contact_id=outreach.contact_id,
        user_id=outreach.user_id,
        channel=outreach.channel.value if hasattr(outreach.channel, 'value') else str(outreach.channel),
        status=outreach.status.value if hasattr(outreach.status, 'value') else str(outreach.status),
        recipient=outreach.recipient,
        subject=outreach.subject,
        notes=outreach.notes,
        metadata_json=outreach.metadata_json,
        attempted_at=outreach.attempted_at.isoformat() if outreach.attempted_at else None,
        created_at=outreach.created_at.isoformat() if outreach.created_at else None
    )

@router.get("/businesses/{business_id}/outreach", response_model=List[OutreachResponse])
async def list_business_outreaches(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    outreaches = await BusinessService.get_business_outreaches(session=session, business_id=business_id)
    return [
        OutreachResponse(
            id=o.id,
            business_id=o.business_id,
            contact_id=o.contact_id,
            user_id=o.user_id,
            channel=o.channel.value if hasattr(o.channel, 'value') else str(o.channel),
            status=o.status.value if hasattr(o.status, 'value') else str(o.status),
            recipient=o.recipient,
            subject=o.subject,
            notes=o.notes,
            metadata_json=o.metadata_json,
            attempted_at=o.attempted_at.isoformat() if o.attempted_at else None,
            created_at=o.created_at.isoformat() if o.created_at else None
        )
        for o in outreaches
    ]

# ─────────────────────────────────────────────────────────────
# 4. INTERACTION (Two-way conversations & engagements)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/interactions", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def log_interaction(
    business_id: int,
    request: InteractionCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Logs a verified two-way conversation/meeting, updates last_contacted_at,
    auto-advances lead stage to 'contacted', and emits an audit Activity.
    """
    interaction = await BusinessService.log_interaction(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user
    )
    return InteractionResponse(
        id=interaction.id,
        business_id=interaction.business_id,
        contact_id=interaction.contact_id,
        user_id=interaction.user_id,
        outreach_id=interaction.outreach_id,
        type=interaction.type.value if hasattr(interaction.type, 'value') else str(interaction.type),
        duration_seconds=interaction.duration_seconds,
        summary=interaction.summary,
        outcome=interaction.outcome,
        sentiment=interaction.sentiment,
        occurred_at=interaction.occurred_at.isoformat() if interaction.occurred_at else None,
        created_at=interaction.created_at.isoformat() if interaction.created_at else None
    )

@router.get("/businesses/{business_id}/interactions", response_model=List[InteractionResponse])
async def list_business_interactions(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    interactions = await BusinessService.get_business_interactions(session=session, business_id=business_id)
    return [
        InteractionResponse(
            id=it.id,
            business_id=it.business_id,
            contact_id=it.contact_id,
            user_id=it.user_id,
            outreach_id=it.outreach_id,
            type=it.type.value if hasattr(it.type, 'value') else str(it.type),
            duration_seconds=it.duration_seconds,
            summary=it.summary,
            outcome=it.outcome,
            sentiment=it.sentiment,
            occurred_at=it.occurred_at.isoformat() if it.occurred_at else None,
            created_at=it.created_at.isoformat() if it.created_at else None
        )
        for it in interactions
    ]

# ─────────────────────────────────────────────────────────────
# 5. NOTES (Dedicated Note Content)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    business_id: int,
    request: NoteCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    note = await BusinessService.create_note(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user
    )
    return NoteResponse(
        id=note.id,
        business_id=note.business_id,
        contact_id=note.contact_id,
        user_id=note.user_id,
        content=note.content,
        created_at=note.created_at.isoformat() if note.created_at else None,
        updated_at=note.updated_at.isoformat() if note.updated_at else None
    )

@router.get("/businesses/{business_id}/notes", response_model=List[NoteResponse])
async def list_business_notes(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    notes = await BusinessService.get_business_notes(session=session, business_id=business_id)
    return [
        NoteResponse(
            id=n.id,
            business_id=n.business_id,
            contact_id=n.contact_id,
            user_id=n.user_id,
            content=n.content,
            created_at=n.created_at.isoformat() if n.created_at else None,
            updated_at=n.updated_at.isoformat() if n.updated_at else None
        )
        for n in notes
    ]

@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Deletes a note record from the database."""
    await BusinessService.delete_note(
        session=session,
        note_id=note_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ─────────────────────────────────────────────────────────────
# 6. TASKS (Actionable Work To-Dos)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    business_id: int,
    request: TaskCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    task = await BusinessService.create_task(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user
    )
    return TaskResponse(
        id=task.id,
        business_id=task.business_id,
        contact_id=task.contact_id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
        status=task.status.value if hasattr(task.status, 'value') else str(task.status),
        due_date=task.due_date.isoformat() if task.due_date else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat() if task.created_at else None
    )

@router.get("/tasks", response_model=List[TaskResponse])
async def list_all_tasks(
    status: Optional[str] = Query(None, description="Filter by status (pending, in_progress, completed, cancelled, all)"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    tasks = await BusinessService.get_all_tasks(
        session=session,
        status=status,
        user_id=current_user.user_id
    )
    return [
        TaskResponse(
            id=t.id,
            business_id=t.business_id,
            contact_id=t.contact_id,
            user_id=t.user_id,
            title=t.title,
            description=t.description,
            priority=t.priority.value if hasattr(t.priority, 'value') else str(t.priority),
            status=t.status.value if hasattr(t.status, 'value') else str(t.status),
            due_date=t.due_date.isoformat() if t.due_date else None,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
            created_at=t.created_at.isoformat() if t.created_at else None
        )
        for t in tasks
    ]

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    task = await BusinessService.update_task(
        session=session,
        task_id=task_id,
        req=request,
        current_user=current_user
    )
    return TaskResponse(
        id=task.id,
        business_id=task.business_id,
        contact_id=task.contact_id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
        status=task.status.value if hasattr(task.status, 'value') else str(task.status),
        due_date=task.due_date.isoformat() if task.due_date else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat() if task.created_at else None
    )

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Deletes a task record from the database."""
    await BusinessService.delete_task(
        session=session,
        task_id=task_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ─────────────────────────────────────────────────────────────
# 7. REMINDERS & FOLLOW-UPS
# ─────────────────────────────────────────────────────────────

def _to_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()

@router.post("/businesses/{business_id}/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    business_id: int,
    request: ReminderCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reminder, business_name = await BusinessService.create_reminder(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user
    )
    return ReminderResponse(
        id=reminder.id,
        business_id=reminder.business_id,
        contact_id=reminder.contact_id,
        user_id=reminder.user_id,
        task_id=reminder.task_id,
        title=reminder.title,
        notes=reminder.notes,
        due_at=_to_utc_iso(reminder.due_at),
        status=reminder.status.value if hasattr(reminder.status, 'value') else str(reminder.status),
        business_name=business_name,
        contact_name=None,
        completed_at=_to_utc_iso(reminder.completed_at),
        created_at=_to_utc_iso(reminder.created_at)
    )

@router.get("/businesses/{business_id}/reminders", response_model=List[ReminderResponse])
async def list_business_reminders(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reminders = await BusinessService.get_business_reminders(
        session=session,
        business_id=business_id,
        user_id=current_user.user_id
    )
    return [
        ReminderResponse(
            id=r.id,
            business_id=r.business_id,
            contact_id=r.contact_id,
            user_id=r.user_id,
            task_id=r.task_id,
            title=r.title,
            notes=r.notes,
            due_at=_to_utc_iso(r.due_at),
            status=r.status.value if hasattr(r.status, 'value') else str(r.status),
            business_name=r.business.business_name if r.business else None,
            contact_name=r.contact.name if r.contact else None,
            completed_at=_to_utc_iso(r.completed_at),
            created_at=_to_utc_iso(r.created_at)
        )
        for r in reminders
    ]

@router.get("/reminders", response_model=List[ReminderResponse])
async def list_all_reminders(
    status: Optional[str] = Query(None, description="Filter by status (pending, completed, cancelled, all)"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reminders = await BusinessService.get_all_reminders(
        session=session,
        status=status,
        user_id=current_user.user_id
    )
    return [
        ReminderResponse(
            id=r.id,
            business_id=r.business_id,
            contact_id=r.contact_id,
            user_id=r.user_id,
            task_id=r.task_id,
            title=r.title,
            notes=r.notes,
            due_at=_to_utc_iso(r.due_at),
            status=r.status.value if hasattr(r.status, 'value') else str(r.status),
            business_name=r.business.business_name if r.business else None,
            contact_name=r.contact.name if r.contact else None,
            completed_at=_to_utc_iso(r.completed_at),
            created_at=_to_utc_iso(r.created_at)
        )
        for r in reminders
    ]

@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    request: ReminderUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reminder = await BusinessService.update_reminder(
        session=session,
        reminder_id=reminder_id,
        req=request,
        current_user=current_user
    )
    return ReminderResponse(
        id=reminder.id,
        business_id=reminder.business_id,
        contact_id=reminder.contact_id,
        user_id=reminder.user_id,
        task_id=reminder.task_id,
        title=reminder.title,
        notes=reminder.notes,
        due_at=_to_utc_iso(reminder.due_at),
        status=reminder.status.value if hasattr(reminder.status, 'value') else str(reminder.status),
        business_name=reminder.business.business_name if reminder.business else None,
        contact_name=reminder.contact.name if reminder.contact else None,
        completed_at=_to_utc_iso(reminder.completed_at),
        created_at=_to_utc_iso(reminder.created_at)
    )

@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Deletes a reminder record from the database."""
    await BusinessService.delete_reminder(
        session=session,
        reminder_id=reminder_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ─────────────────────────────────────────────────────────────
# 8. ACTIVITIES (Chronological Timeline Audit Stream)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_business_activity(
    business_id: int,
    request: ActivityCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Logs an activity (e.g. website visit, call, outreach, note) for a business.
    """
    res = await BusinessService.create_activity(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user
    )
    act = res["activity"]
    return ActivityResponse(
        id=act.id,
        business_id=act.business_id,
        user_id=act.user_id,
        user_name=res["user_name"],
        contact_id=act.contact_id,
        type=act.type.value if hasattr(act.type, 'value') else str(act.type),
        channel=act.channel,
        outcome=act.outcome,
        notes=act.notes,
        entity_type=act.entity_type,
        entity_id=act.entity_id,
        created_at=act.created_at.isoformat() if act.created_at else None
    )

@router.get("/businesses/{business_id}/activities", response_model=List[ActivityResponse])
async def list_business_activities(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    enriched = await BusinessService.get_business_activities(session=session, business_id=business_id)
    return [
        ActivityResponse(
            id=row["activity"].id,
            business_id=row["activity"].business_id,
            user_id=row["activity"].user_id,
            user_name=row["user_name"],
            contact_id=row["activity"].contact_id,
            type=row["activity"].type.value if hasattr(row["activity"].type, 'value') else str(row["activity"].type),
            channel=row["activity"].channel,
            outcome=row["activity"].outcome,
            notes=row["activity"].notes,
            entity_type=row["activity"].entity_type,
            entity_id=row["activity"].entity_id,
            created_at=row["activity"].created_at.isoformat() if row["activity"].created_at else None
        )
        for row in enriched
    ]

@router.get("/activities", response_model=List[ActivityResponse])
async def list_all_activities(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    enriched = await BusinessService.get_all_activities(
        session=session,
        limit=limit,
        user_id=current_user.user_id
    )
    return [
        ActivityResponse(
            id=row["activity"].id,
            business_id=row["activity"].business_id,
            user_id=row["activity"].user_id,
            user_name=row["user_name"],
            contact_id=row["activity"].contact_id,
            type=row["activity"].type.value if hasattr(row["activity"].type, 'value') else str(row["activity"].type),
            channel=row["activity"].channel,
            outcome=row["activity"].outcome,
            notes=row["activity"].notes,
            entity_type=row["activity"].entity_type,
            entity_id=row["activity"].entity_id,
            created_at=row["activity"].created_at.isoformat() if row["activity"].created_at else None
        )
        for row in enriched
    ]

@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Deletes an activity timeline entry.
    """
    await BusinessService.delete_activity(
        session=session,
        activity_id=activity_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ─────────────────────────────────────────────────────────────
# 9. CONTACTS (Multi-account decision makers & stakeholders)
# ─────────────────────────────────────────────────────────────

@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Lists contacts across accounts/businesses with optional search filtering.
    """
    return await BusinessService.list_contacts(
        session=session,
        skip=skip,
        limit=limit,
        search=search
    )

@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Deletes a single contact and clears references in associated records.
    """
    await BusinessService.delete_contact(
        session=session,
        contact_id=contact_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────
# 11. PROSPECT DEMO MANAGEMENT (Sales CRM Token Generation)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/demo", response_model=DemoResponse)
async def create_or_get_prospect_demo(
    business_id: int,
    background_tasks: BackgroundTasks,
    body: Optional[DemoCreateRequest] = None,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate or retrieve the secure demo link for a prospect.
    Creates an unguessable 24-character token bound to this business.
    1. Inspects prospect source and available data.
    2. Performs corroborated website intelligence lookup & reuse (or fresh crawl).
    3. Personalizes the demo with authentic branding, doctors, services, and content.
    """
    stmt_bus = (
        select(Business)
        .where(Business.id == business_id)
        .options(
            selectinload(Business.sources),
            selectinload(Business.demos),
        )
    )
    res_bus = await session.execute(stmt_bus)
    business = res_bus.scalars().first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # 1. Corroborated website intelligence retrieval (or cache reuse)
    profile: Optional[EnrichedBusinessProfile] = None
    is_cached = False
    if business.website:
        profile, is_cached = await EnrichmentService.get_or_enrich_website(
            prospect=business,
            session=session
        )

    # 2. Check for existing active demo
    stmt_demo = select(ProspectDemo).where(
        and_(ProspectDemo.business_id == business_id, ProspectDemo.status == "active")
    ).order_by(ProspectDemo.created_at.desc())
    res_demo = await session.execute(stmt_demo)
    demo = res_demo.scalars().first()

    base_overrides = body.custom_overrides if body and body.custom_overrides else {}
    if profile:
        merged_overrides = EnrichmentService.personalize_demo_overrides(
            prospect=business,
            profile=profile,
            existing_overrides=base_overrides
        )
    else:
        merged_overrides = base_overrides or None

    if not demo:
        token = secrets.token_urlsafe(24)
        demo = ProspectDemo(
            business_id=business_id,
            token=token,
            status="active",
            template_id="dental-default",
            custom_overrides=merged_overrides,
            created_by_user_id=current_user.user_id
        )
        session.add(demo)
        await session.commit()
        await session.refresh(demo)
    else:
        # Update existing demo with personalized overrides
        if merged_overrides:
            existing = dict(demo.custom_overrides or {})
            existing.update(merged_overrides)
            demo.custom_overrides = existing
            await session.commit()
            await session.refresh(demo)

    # Fallback to background enrichment if live crawl was skipped or timed out
    if business.website and not profile:
        background_tasks.add_task(
            EnrichmentService.enrich_business_background,
            business_id=business.id
        )

    base_url = settings.DEMO_BASE_URL.rstrip("/")
    demo_url = f"{base_url}/{demo.token}"

    return DemoResponse(
        id=demo.id,
        business_id=demo.business_id,
        token=demo.token,
        demo_url=demo_url,
        status=demo.status,
        template_id=demo.template_id,
        custom_overrides=demo.custom_overrides,
        view_count=demo.view_count,
        last_viewed_at=demo.last_viewed_at,
        created_at=demo.created_at,
        updated_at=demo.updated_at
    )


@router.get("/businesses/{business_id}/demo", response_model=DemoResponse)
async def get_business_demo(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Fetch current demo link and engagement metrics for a business.
    """
    stmt = select(ProspectDemo).where(
        and_(ProspectDemo.business_id == business_id, ProspectDemo.status == "active")
    ).order_by(ProspectDemo.created_at.desc())
    res = await session.execute(stmt)
    demo = res.scalars().first()

    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active demo found for this business"
        )

    base_url = settings.DEMO_BASE_URL.rstrip("/")
    demo_url = f"{base_url}/{demo.token}"

    return DemoResponse(
        id=demo.id,
        business_id=demo.business_id,
        token=demo.token,
        demo_url=demo_url,
        status=demo.status,
        template_id=demo.template_id,
        custom_overrides=demo.custom_overrides,
        view_count=demo.view_count,
        last_viewed_at=demo.last_viewed_at,
        created_at=demo.created_at,
        updated_at=demo.updated_at
    )


# ─────────────────────────────────────────────────────────────
# 12. PROSPECT ENRICHMENT (Asynchronous Website Intelligence)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/enrichment", response_model=EnrichmentTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_business_enrichment(
    business_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Triggers asynchronous website enrichment for a business.
    Extracts branding, doctor credentials, treatments, contact, and tech stack.
    """
    business = await session.get(Business, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    if not business.website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business does not have a website URL to enrich"
        )

    background_tasks.add_task(
        EnrichmentService.enrich_business_background,
        business_id=business.id
    )

    return EnrichmentTriggerResponse(
        business_id=business.id,
        status="queued",
        message=f"Enrichment task queued for {business.website}"
    )


@router.get("/businesses/{business_id}/enrichment", response_model=BusinessEnrichmentStatusResponse)
async def get_business_enrichment(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Fetches the enriched profile and quality audit results for a business.
    """
    stmt = (
        select(Business)
        .where(Business.id == business_id)
        .options(selectinload(Business.sources))
        .execution_options(populate_existing=True)
    )
    res = await session.execute(stmt)
    business = res.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    profile = EnrichmentService.extract_enrichment_from_business(business)
    if not profile:
        return BusinessEnrichmentStatusResponse(
            business_id=business.id,
            is_enriched=False,
            treatments_count=0
        )

    return BusinessEnrichmentStatusResponse(
        business_id=business.id,
        is_enriched=True,
        enriched_at=profile.extracted_at,
        quality_score=profile.quality.score if profile.quality else None,
        brand=profile.brand,
        primary_doctor=profile.primary_doctor,
        treatments_count=len(profile.treatments),
        profile=profile
    )
