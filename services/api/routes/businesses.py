from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
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
    ActivityResponse,
)
from schemas.auth import TokenData
from services.auth_service import get_current_user
from services.business_service import BusinessService

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

@router.post("/prospects/{business_id}/add-to-leads", response_model=BusinessResponse)
async def add_prospect_to_leads(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Promotes a prospect into the active sales pipeline, creating its Lead record.
    """
    return await BusinessService.add_to_leads(
        session=session,
        business_id=business_id,
        current_user=current_user
    )

@router.post("/prospects/bulk-add-to-leads", response_model=BulkAddToLeadsResponse)
async def bulk_add_prospects_to_leads(
    req: BulkAddToLeadsRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Bulk promotes multiple prospects into active sales Leads.
    """
    return await BusinessService.bulk_add_to_leads(
        session=session,
        business_ids=req.business_ids,
        current_user=current_user
    )

@router.patch("/prospects/{business_id}/qualify", response_model=BusinessResponse)
async def qualify_prospect(
    business_id: int,
    req: QualifyProspectRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Updates the qualification status for a prospect.
    """
    return await BusinessService.qualify_prospect(
        session=session,
        business_id=business_id,
        qualification_status=req.qualification_status,
        current_user=current_user
    )

# ─────────────────────────────────────────────────────────────
# 2. LEADS (Businesses in active sales pipeline)
# ─────────────────────────────────────────────────────────────

@router.get("/businesses", response_model=List[BusinessResponse])
@router.get("/leads", response_model=List[BusinessResponse])
async def list_businesses(
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
    Returns a paginated list of leads with active sales records.
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

@router.get("/businesses/{business_id}", response_model=BusinessResponse)
@router.get("/leads/{business_id}", response_model=BusinessResponse)
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
@router.patch("/leads/{business_id}", response_model=BusinessResponse)
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

@router.delete("/businesses/{business_id}")
@router.delete("/leads/{business_id}")
@router.delete("/prospects/{business_id}")
async def delete_business(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Deletes a business/lead record from the database.
    """
    return await BusinessService.delete_business(
        session=session,
        business_id=business_id,
        current_user=current_user
    )

@router.post("/businesses/bulk-delete", response_model=BulkDeleteResponse)
@router.post("/leads/bulk-delete", response_model=BulkDeleteResponse)
@router.post("/prospects/bulk-delete", response_model=BulkDeleteResponse)
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

@router.patch("/businesses/{business_id}/stage", response_model=StageUpdateResponse)
@router.patch("/leads/{business_id}/stage", response_model=StageUpdateResponse)
async def update_pipeline_stage(
    business_id: int,
    update: StageUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Updates the pipeline stage for a business/lead and records an audit activity.
    """
    return await BusinessService.update_pipeline_stage(
        session=session,
        business_id=business_id,
        new_stage=update.stage,
        current_user=current_user
    )

# ─────────────────────────────────────────────────────────────
# 3. OUTREACH (What we attempted)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/outreach", response_model=OutreachResponse)
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

@router.post("/businesses/{business_id}/interactions", response_model=InteractionResponse)
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

@router.post("/businesses/{business_id}/notes", response_model=NoteResponse)
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

@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Deletes a note record from the database."""
    return await BusinessService.delete_note(
        session=session,
        note_id=note_id,
        current_user=current_user
    )

# ─────────────────────────────────────────────────────────────
# 6. TASKS (Actionable Work To-Dos)
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/tasks", response_model=TaskResponse)
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

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Deletes a task record from the database."""
    return await BusinessService.delete_task(
        session=session,
        task_id=task_id,
        current_user=current_user
    )

# ─────────────────────────────────────────────────────────────
# 7. REMINDERS & FOLLOW-UPS
# ─────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/reminders", response_model=ReminderResponse)
async def create_reminder(
    business_id: int,
    request: ReminderCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reminder = await BusinessService.create_reminder(
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
        due_at=reminder.due_at.isoformat() if reminder.due_at else None,
        status=reminder.status.value if hasattr(reminder.status, 'value') else str(reminder.status),
        completed_at=reminder.completed_at.isoformat() if reminder.completed_at else None,
        created_at=reminder.created_at.isoformat() if reminder.created_at else None
    )

@router.get("/reminders", response_model=List[ReminderResponse])
@router.get("/follow-ups", response_model=List[ReminderResponse])
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
            due_at=r.due_at.isoformat() if r.due_at else None,
            status=r.status.value if hasattr(r.status, 'value') else str(r.status),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            created_at=r.created_at.isoformat() if r.created_at else None
        )
        for r in reminders
    ]

@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
@router.patch("/follow-ups/{reminder_id}", response_model=ReminderResponse)
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
        due_at=reminder.due_at.isoformat() if reminder.due_at else None,
        status=reminder.status.value if hasattr(reminder.status, 'value') else str(reminder.status),
        completed_at=reminder.completed_at.isoformat() if reminder.completed_at else None,
        created_at=reminder.created_at.isoformat() if reminder.created_at else None
    )

@router.delete("/reminders/{reminder_id}")
@router.delete("/follow-ups/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Deletes a reminder record from the database."""
    return await BusinessService.delete_reminder(
        session=session,
        reminder_id=reminder_id,
        current_user=current_user
    )

# ─────────────────────────────────────────────────────────────
# 8. ACTIVITIES (Chronological Timeline Audit Stream)
# ─────────────────────────────────────────────────────────────

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
