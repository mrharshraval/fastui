"""FastUI Engagement Domain API Routes.

Exposes RESTful endpoints for CRM engagement: notes, tasks, reminders, outreaches,
interactions, chronological activity audits, and contacts.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.models import User
from app.domains.engagement.schemas import (
    ActivityCreateRequest,
    ActivityResponse,
    ContactResponse,
    InteractionCreateRequest,
    InteractionResponse,
    NoteCreateRequest,
    NoteResponse,
    OutreachCreateRequest,
    OutreachResponse,
    ReminderCreateRequest,
    ReminderResponse,
    ReminderUpdateRequest,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from app.domains.engagement.service import EngagementService

router = APIRouter(tags=["Engagement"])


def _to_utc_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.isoformat()


# ─────────────────────────────────────────────────────────────
# 1. NOTES
# ─────────────────────────────────────────────────────────────
@router.post(
    "/businesses/{business_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Note",
)
async def create_note(
    business_id: int,
    request: NoteCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    """Creates a sales note for a business."""
    note = await EngagementService.create_note(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user,
    )
    return NoteResponse(
        id=note.id,
        business_id=note.business_id,
        contact_id=note.contact_id,
        user_id=note.user_id,
        content=note.content,
        created_at=_to_utc_iso(note.created_at),
        updated_at=_to_utc_iso(note.updated_at),
    )


@router.get(
    "/businesses/{business_id}/notes",
    response_model=list[NoteResponse],
    summary="List Business Notes",
)
async def list_business_notes(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NoteResponse]:
    """Lists all notes attached to a specific business."""
    notes = await EngagementService.get_business_notes(session=session, business_id=business_id)
    return [
        NoteResponse(
            id=n.id,
            business_id=n.business_id,
            contact_id=n.contact_id,
            user_id=n.user_id,
            content=n.content,
            created_at=_to_utc_iso(n.created_at),
            updated_at=_to_utc_iso(n.updated_at),
        )
        for n in notes
    ]


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Note",
)
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Deletes a note."""
    await EngagementService.delete_note(
        session=session,
        note_id=note_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────
# 2. TASKS
# ─────────────────────────────────────────────────────────────
@router.post(
    "/businesses/{business_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Task",
)
async def create_task(
    business_id: int,
    request: TaskCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Creates an actionable task for a business."""
    task = await EngagementService.create_task(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user,
    )
    return TaskResponse(
        id=task.id,
        business_id=task.business_id,
        contact_id=task.contact_id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        priority=task.priority if isinstance(task.priority, str) else str(task.priority),
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        due_date=_to_utc_iso(task.due_date),
        completed_at=_to_utc_iso(task.completed_at),
        created_at=_to_utc_iso(task.created_at),
    )


@router.get(
    "/tasks",
    response_model=list[TaskResponse],
    summary="List All Tasks",
)
async def list_all_tasks(
    status: str | None = Query(
        None, description="Filter by status (pending, in_progress, completed, cancelled, all)"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """Lists tasks assigned to the current user."""
    tasks = await EngagementService.get_all_tasks(
        session=session,
        status=status,
        user_id=current_user.id,
    )
    return [
        TaskResponse(
            id=t.id,
            business_id=t.business_id,
            contact_id=t.contact_id,
            user_id=t.user_id,
            title=t.title,
            description=t.description,
            priority=t.priority if isinstance(t.priority, str) else str(t.priority),
            status=t.status.value if hasattr(t.status, "value") else str(t.status),
            due_date=_to_utc_iso(t.due_date),
            completed_at=_to_utc_iso(t.completed_at),
            created_at=_to_utc_iso(t.created_at),
        )
        for t in tasks
    ]


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update Task",
)
async def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Updates task status, details, priority, or due date."""
    task = await EngagementService.update_task(
        session=session,
        task_id=task_id,
        req=request,
        current_user=current_user,
    )
    return TaskResponse(
        id=task.id,
        business_id=task.business_id,
        contact_id=task.contact_id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        priority=task.priority if isinstance(task.priority, str) else str(task.priority),
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        due_date=_to_utc_iso(task.due_date),
        completed_at=_to_utc_iso(task.completed_at),
        created_at=_to_utc_iso(task.created_at),
    )


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task",
)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Deletes a task."""
    await EngagementService.delete_task(
        session=session,
        task_id=task_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────
# 3. REMINDERS & FOLLOW-UPS
# ─────────────────────────────────────────────────────────────
@router.post(
    "/businesses/{business_id}/reminders",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Reminder",
)
async def create_reminder(
    business_id: int,
    request: ReminderCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderResponse:
    """Creates a scheduled reminder with automated push notifications."""
    reminder, business_name = await EngagementService.create_reminder(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user,
    )
    return ReminderResponse(
        id=reminder.id,
        business_id=reminder.business_id,
        contact_id=reminder.contact_id,
        user_id=reminder.user_id,
        task_id=reminder.task_id,
        title=reminder.title,
        notes=reminder.notes,
        due_at=_to_utc_iso(reminder.due_at) or "",
        status=reminder.status.value if hasattr(reminder.status, "value") else str(reminder.status),
        business_name=business_name,
        contact_name=None,
        completed_at=_to_utc_iso(reminder.completed_at),
        created_at=_to_utc_iso(reminder.created_at),
    )


@router.get(
    "/businesses/{business_id}/reminders",
    response_model=list[ReminderResponse],
    summary="List Business Reminders",
)
async def list_business_reminders(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReminderResponse]:
    """Lists all reminders for a specific business."""
    reminders = await EngagementService.get_business_reminders(
        session=session,
        business_id=business_id,
        user_id=current_user.id,
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
            due_at=_to_utc_iso(r.due_at) or "",
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            business_name=r.business.business_name if r.business else None,
            contact_name=f"{r.contact.first_name or ''} {r.contact.last_name or ''}".strip()
            if r.contact
            else None,
            completed_at=_to_utc_iso(r.completed_at),
            created_at=_to_utc_iso(r.created_at),
        )
        for r in reminders
    ]


@router.get(
    "/reminders",
    response_model=list[ReminderResponse],
    summary="List All Reminders",
)
async def list_all_reminders(
    status: str | None = Query(
        None, description="Filter by status (pending, completed, cancelled, all)"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReminderResponse]:
    """Lists all reminders for the authenticated user."""
    reminders = await EngagementService.get_all_reminders(
        session=session,
        status=status,
        user_id=current_user.id,
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
            due_at=_to_utc_iso(r.due_at) or "",
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            business_name=r.business.business_name if r.business else None,
            contact_name=f"{r.contact.first_name or ''} {r.contact.last_name or ''}".strip()
            if r.contact
            else None,
            completed_at=_to_utc_iso(r.completed_at),
            created_at=_to_utc_iso(r.created_at),
        )
        for r in reminders
    ]


@router.patch(
    "/reminders/{reminder_id}",
    response_model=ReminderResponse,
    summary="Update Reminder",
)
async def update_reminder(
    reminder_id: int,
    request: ReminderUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderResponse:
    """Updates status, title, notes, or scheduled timestamp for a reminder."""
    reminder = await EngagementService.update_reminder(
        session=session,
        reminder_id=reminder_id,
        req=request,
        current_user=current_user,
    )
    return ReminderResponse(
        id=reminder.id,
        business_id=reminder.business_id,
        contact_id=reminder.contact_id,
        user_id=reminder.user_id,
        task_id=reminder.task_id,
        title=reminder.title,
        notes=reminder.notes,
        due_at=_to_utc_iso(reminder.due_at) or "",
        status=reminder.status.value if hasattr(reminder.status, "value") else str(reminder.status),
        business_name=reminder.business.business_name if reminder.business else None,
        contact_name=f"{reminder.contact.first_name or ''} {reminder.contact.last_name or ''}".strip()
        if reminder.contact
        else None,
        completed_at=_to_utc_iso(reminder.completed_at),
        created_at=_to_utc_iso(reminder.created_at),
    )


@router.delete(
    "/reminders/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Reminder",
)
async def delete_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Deletes a reminder record."""
    await EngagementService.delete_reminder(
        session=session,
        reminder_id=reminder_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────
# 4. OUTREACH
# ─────────────────────────────────────────────────────────────
@router.post(
    "/businesses/{business_id}/outreach",
    response_model=OutreachResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log Outreach",
)
async def log_outreach(
    business_id: int,
    request: OutreachCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OutreachResponse:
    """Logs an outbound communication attempt (call, WhatsApp, email)."""
    outreach = await EngagementService.log_outreach(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user,
    )
    return OutreachResponse(
        id=outreach.id,
        business_id=outreach.business_id,
        contact_id=outreach.contact_id,
        user_id=outreach.user_id,
        channel=outreach.channel.value
        if hasattr(outreach.channel, "value")
        else str(outreach.channel),
        status=outreach.status.value if hasattr(outreach.status, "value") else str(outreach.status),
        recipient=outreach.recipient,
        subject=outreach.subject,
        notes=outreach.notes,
        metadata_json=outreach.metadata_json,
        attempted_at=_to_utc_iso(outreach.attempted_at),
        created_at=_to_utc_iso(outreach.created_at),
    )


@router.get(
    "/businesses/{business_id}/outreach",
    response_model=list[OutreachResponse],
    summary="List Business Outreaches",
)
async def list_business_outreaches(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OutreachResponse]:
    """Lists all outreach attempts for a business."""
    outreaches = await EngagementService.get_business_outreaches(
        session=session, business_id=business_id
    )
    return [
        OutreachResponse(
            id=o.id,
            business_id=o.business_id,
            contact_id=o.contact_id,
            user_id=o.user_id,
            channel=o.channel.value if hasattr(o.channel, "value") else str(o.channel),
            status=o.status.value if hasattr(o.status, "value") else str(o.status),
            recipient=o.recipient,
            subject=o.subject,
            notes=o.notes,
            metadata_json=o.metadata_json,
            attempted_at=_to_utc_iso(o.attempted_at),
            created_at=_to_utc_iso(o.created_at),
        )
        for o in outreaches
    ]


# ─────────────────────────────────────────────────────────────
# 5. INTERACTIONS
# ─────────────────────────────────────────────────────────────
@router.post(
    "/businesses/{business_id}/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log Interaction",
)
async def log_interaction(
    business_id: int,
    request: InteractionCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InteractionResponse:
    """Logs a completed 2-way conversation or meeting."""
    interaction = await EngagementService.log_interaction(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user,
    )
    return InteractionResponse(
        id=interaction.id,
        business_id=interaction.business_id,
        contact_id=interaction.contact_id,
        user_id=interaction.user_id,
        outreach_id=interaction.outreach_id,
        type=interaction.type.value
        if hasattr(interaction.type, "value")
        else str(interaction.type),
        duration_seconds=interaction.duration_seconds,
        summary=interaction.summary,
        outcome=interaction.outcome,
        sentiment=interaction.sentiment,
        occurred_at=_to_utc_iso(interaction.occurred_at),
        created_at=_to_utc_iso(interaction.created_at),
    )


@router.get(
    "/businesses/{business_id}/interactions",
    response_model=list[InteractionResponse],
    summary="List Business Interactions",
)
async def list_business_interactions(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InteractionResponse]:
    """Lists all completed interactions logged for a business."""
    interactions = await EngagementService.get_business_interactions(
        session=session, business_id=business_id
    )
    return [
        InteractionResponse(
            id=i.id,
            business_id=i.business_id,
            contact_id=i.contact_id,
            user_id=i.user_id,
            outreach_id=i.outreach_id,
            type=i.type.value if hasattr(i.type, "value") else str(i.type),
            duration_seconds=i.duration_seconds,
            summary=i.summary,
            outcome=i.outcome,
            sentiment=i.sentiment,
            occurred_at=_to_utc_iso(i.occurred_at),
            created_at=_to_utc_iso(i.created_at),
        )
        for i in interactions
    ]


# ─────────────────────────────────────────────────────────────
# 6. ACTIVITIES (Timeline Audit Stream)
# ─────────────────────────────────────────────────────────────
@router.post(
    "/businesses/{business_id}/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Activity",
)
async def create_business_activity(
    business_id: int,
    request: ActivityCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivityResponse:
    """Logs an activity audit entry for a business."""
    res = await EngagementService.create_activity(
        session=session,
        business_id=business_id,
        req=request,
        current_user=current_user,
    )
    act = res["activity"]
    return ActivityResponse(
        id=act.id,
        business_id=act.business_id,
        user_id=act.user_id,
        user_name=res["user_name"],
        contact_id=act.contact_id,
        type=act.type.value if hasattr(act.type, "value") else str(act.type),
        channel=act.channel,
        outcome=act.outcome,
        notes=act.notes,
        entity_type=act.entity_type,
        entity_id=act.entity_id,
        created_at=_to_utc_iso(act.created_at),
    )


@router.get(
    "/businesses/{business_id}/activities",
    response_model=list[ActivityResponse],
    summary="List Business Activities",
)
async def list_business_activities(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ActivityResponse]:
    """Lists chronological audit timeline events for a business."""
    enriched = await EngagementService.get_business_activities(
        session=session, business_id=business_id
    )
    return [
        ActivityResponse(
            id=row["activity"].id,
            business_id=row["activity"].business_id,
            user_id=row["activity"].user_id,
            user_name=row["user_name"],
            contact_id=row["activity"].contact_id,
            type=row["activity"].type.value
            if hasattr(row["activity"].type, "value")
            else str(row["activity"].type),
            channel=row["activity"].channel,
            outcome=row["activity"].outcome,
            notes=row["activity"].notes,
            entity_type=row["activity"].entity_type,
            entity_id=row["activity"].entity_id,
            created_at=_to_utc_iso(row["activity"].created_at),
        )
        for row in enriched
    ]


@router.get(
    "/activities",
    response_model=list[ActivityResponse],
    summary="List All Activities",
)
async def list_all_activities(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ActivityResponse]:
    """Lists global activities across businesses scoped to current user."""
    enriched = await EngagementService.get_all_activities(
        session=session,
        limit=limit,
        user_id=current_user.id,
    )
    return [
        ActivityResponse(
            id=row["activity"].id,
            business_id=row["activity"].business_id,
            user_id=row["activity"].user_id,
            user_name=row["user_name"],
            contact_id=row["activity"].contact_id,
            type=row["activity"].type.value
            if hasattr(row["activity"].type, "value")
            else str(row["activity"].type),
            channel=row["activity"].channel,
            outcome=row["activity"].outcome,
            notes=row["activity"].notes,
            entity_type=row["activity"].entity_type,
            entity_id=row["activity"].entity_id,
            created_at=_to_utc_iso(row["activity"].created_at),
        )
        for row in enriched
    ]


@router.delete(
    "/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Activity",
)
async def delete_activity(
    activity_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Deletes an activity audit record."""
    await EngagementService.delete_activity(
        session=session,
        activity_id=activity_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────
# 7. CONTACTS
# ─────────────────────────────────────────────────────────────
@router.get(
    "/contacts",
    response_model=list[ContactResponse],
    summary="List Contacts",
)
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ContactResponse]:
    """Lists stakeholder contacts across businesses."""
    contacts_data = await EngagementService.list_contacts(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
    )
    return [ContactResponse.model_validate(c) for c in contacts_data]


@router.delete(
    "/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Contact",
)
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Deletes a contact and clears associated foreign keys."""
    await EngagementService.delete_contact(
        session=session,
        contact_id=contact_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
