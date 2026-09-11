"""FastUI Engagement Domain Services.

Handles CRM touchpoints, notes, tasks, reminders, outreaches, interactions,
chronological activity audits, contact management, and push notification dispatch.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import asc, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.auth.models import User
from app.domains.businesses.models import Business
from app.domains.engagement.models import (
    Activity,
    ActivityType,
    Contact,
    Interaction,
    InteractionType,
    Note,
    Outreach,
    OutreachChannel,
    OutreachStatus,
    Reminder,
    ReminderStatus,
    Task,
    TaskStatus,
)
from app.domains.engagement.schemas import (
    ActivityCreateRequest,
    InteractionCreateRequest,
    NoteCreateRequest,
    OutreachCreateRequest,
    ReminderCreateRequest,
    ReminderUpdateRequest,
    TaskCreateRequest,
    TaskUpdateRequest,
)
from app.domains.leads.models import Lead, LeadPriority, PipelineStage
from app.domains.notifications.models import PushSubscription
from app.domains.notifications.service import NotificationService
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger("fastui.engagement")


class EngagementService:
    """Unified service for all CRM interactions, notes, tasks, reminders, and activities."""

    # ─────────────────────────────────────────────────────────────
    # NOTES
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_note(
        session: AsyncSession,
        business_id: int,
        req: NoteCreateRequest,
        current_user: User,
    ) -> Note:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        note = Note(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.id,
            content=req.content,
        )
        session.add(note)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.id,
            contact_id=req.contact_id,
            type=ActivityType.NOTE_ADDED,
            channel="note",
            outcome="Note added",
            notes=req.content,
            entity_type="note",
            entity_id=note.id,
            created_at=datetime.now(UTC),
        )
        session.add(activity)

        await session.commit()
        await session.refresh(note)
        return note

    @staticmethod
    async def get_business_notes(session: AsyncSession, business_id: int) -> list[Note]:
        stmt = select(Note).where(Note.business_id == business_id).order_by(desc(Note.created_at))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_note(
        session: AsyncSession,
        note_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        note = await session.get(Note, note_id)
        if not note:
            raise EntityNotFoundError("Note", note_id)
        await session.delete(note)
        await session.commit()
        logger.info(f"Deleted note ID {note_id} by user {current_user.email}")
        return {"status": "deleted", "id": note_id}

    # ─────────────────────────────────────────────────────────────
    # TASKS
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_task(
        session: AsyncSession,
        business_id: int,
        req: TaskCreateRequest,
        current_user: User,
    ) -> Task:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        priority = "medium"
        if req.priority:
            req_p = req.priority.lower()
            if req_p in [p.value for p in LeadPriority]:
                priority = req_p

        due_date_dt: datetime | None = None
        if isinstance(req.due_date, datetime):
            due_date_dt = (
                req.due_date.replace(tzinfo=UTC)
                if req.due_date.tzinfo is None
                else req.due_date.astimezone(UTC)
            )
        elif isinstance(req.due_date, str) and req.due_date.strip():
            try:
                parsed = datetime.fromisoformat(req.due_date.strip().replace("Z", "+00:00"))
                due_date_dt = (
                    parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
                )
            except Exception:
                due_date_dt = None

        task = Task(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.id,
            title=req.title,
            description=req.description,
            priority=priority,
            status=TaskStatus.PENDING,
            due_date=due_date_dt,
        )
        session.add(task)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.id,
            contact_id=req.contact_id,
            type=ActivityType.TASK_CREATED,
            channel="task",
            outcome="Task created",
            notes=req.title,
            entity_type="task",
            entity_id=task.id,
            created_at=datetime.now(UTC),
        )
        session.add(activity)

        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def update_task(
        session: AsyncSession,
        task_id: int,
        req: TaskUpdateRequest,
        current_user: User,
    ) -> Task:
        task = await session.get(Task, task_id)
        if not task:
            raise EntityNotFoundError("Task", task_id)

        if req.title is not None:
            task.title = req.title
        if req.description is not None:
            task.description = req.description
        if req.priority is not None:
            req_p = req.priority.lower()
            if req_p in [p.value for p in LeadPriority]:
                task.priority = req_p

        if req.due_date is not None:
            if isinstance(req.due_date, datetime):
                task.due_date = (
                    req.due_date.replace(tzinfo=UTC)
                    if req.due_date.tzinfo is None
                    else req.due_date.astimezone(UTC)
                )
            elif isinstance(req.due_date, str) and req.due_date.strip():
                try:
                    parsed = datetime.fromisoformat(req.due_date.strip().replace("Z", "+00:00"))
                    task.due_date = (
                        parsed.replace(tzinfo=UTC)
                        if parsed.tzinfo is None
                        else parsed.astimezone(UTC)
                    )
                except Exception:
                    pass

        if req.status is not None:
            for st in TaskStatus:
                if st.value == req.status.lower():
                    task.status = st
                    if st == TaskStatus.COMPLETED:
                        task.completed_at = datetime.now(UTC)
                        activity = Activity(
                            business_id=task.business_id,
                            user_id=current_user.id,
                            contact_id=task.contact_id,
                            type=ActivityType.TASK_COMPLETED,
                            channel="task",
                            outcome="Task completed",
                            notes=task.title,
                            entity_type="task",
                            entity_id=task.id,
                            created_at=datetime.now(UTC),
                        )
                        session.add(activity)
                    break

        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def get_all_tasks(
        session: AsyncSession,
        status: str | None = None,
        user_id: int | None = None,
    ) -> list[Task]:
        """Returns tasks scoped to the authenticated user."""
        stmt = select(Task)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        if status and status.lower() != "all":
            for st in TaskStatus:
                if st.value == status.lower():
                    stmt = stmt.where(Task.status == st)
                    break
        stmt = stmt.order_by(asc(Task.due_date))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_task(
        session: AsyncSession,
        task_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        task = await session.get(Task, task_id)
        if not task:
            raise EntityNotFoundError("Task", task_id)
        await session.delete(task)
        await session.commit()
        logger.info(f"Deleted task ID {task_id} by user {current_user.email}")
        return {"status": "deleted", "id": task_id}

    # ─────────────────────────────────────────────────────────────
    # REMINDERS
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_reminder(
        session: AsyncSession,
        business_id: int,
        req: ReminderCreateRequest,
        current_user: User,
    ) -> tuple[Reminder, str | None]:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        business_name: str | None = getattr(business, "business_name", None)

        if isinstance(req.due_at, datetime):
            due_at_dt = (
                req.due_at.replace(tzinfo=UTC)
                if req.due_at.tzinfo is None
                else req.due_at.astimezone(UTC)
            )
        elif isinstance(req.due_at, str):
            try:
                raw_str = req.due_at.strip().replace("Z", "+00:00")
                parsed_dt = datetime.fromisoformat(raw_str)
                due_at_dt = (
                    parsed_dt.replace(tzinfo=UTC)
                    if parsed_dt.tzinfo is None
                    else parsed_dt.astimezone(UTC)
                )
            except Exception:
                due_at_dt = datetime.now(UTC)
        else:
            due_at_dt = datetime.now(UTC)

        reminder = Reminder(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.id,
            task_id=req.task_id,
            title=req.title,
            notes=req.notes,
            due_at=due_at_dt,
            status=ReminderStatus.PENDING,
        )
        session.add(reminder)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.id,
            contact_id=req.contact_id,
            type=ActivityType.REMINDER_CREATED,
            channel="reminder",
            outcome="Reminder scheduled",
            notes=f"{req.title} - due {due_at_dt.strftime('%b %d, %I:%M %p')}",
            entity_type="reminder",
            entity_id=reminder.id,
            created_at=datetime.now(UTC),
        )
        session.add(activity)

        await session.commit()
        await session.refresh(reminder)
        return reminder, business_name

    @staticmethod
    async def update_reminder(
        session: AsyncSession,
        reminder_id: int,
        req: ReminderUpdateRequest,
        current_user: User,
    ) -> Reminder:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder:
            raise EntityNotFoundError("Reminder", reminder_id)

        if req.title is not None:
            reminder.title = req.title
        if req.notes is not None:
            reminder.notes = req.notes
        if req.due_at is not None:
            if isinstance(req.due_at, datetime):
                reminder.due_at = (
                    req.due_at.replace(tzinfo=UTC)
                    if req.due_at.tzinfo is None
                    else req.due_at.astimezone(UTC)
                )
            elif isinstance(req.due_at, str) and req.due_at.strip():
                try:
                    raw_str = req.due_at.strip().replace("Z", "+00:00")
                    parsed_dt = datetime.fromisoformat(raw_str)
                    reminder.due_at = (
                        parsed_dt.replace(tzinfo=UTC)
                        if parsed_dt.tzinfo is None
                        else parsed_dt.astimezone(UTC)
                    )
                except Exception:
                    pass

        if req.status is not None:
            for st in ReminderStatus:
                if st.value == req.status.lower():
                    reminder.status = st
                    if st == ReminderStatus.COMPLETED:
                        reminder.completed_at = datetime.now(UTC)
                        activity = Activity(
                            business_id=reminder.business_id,
                            user_id=current_user.id,
                            contact_id=reminder.contact_id,
                            type=ActivityType.REMINDER_COMPLETED,
                            channel="reminder",
                            outcome="Reminder completed",
                            notes=reminder.title,
                            entity_type="reminder",
                            entity_id=reminder.id,
                            created_at=datetime.now(UTC),
                        )
                        session.add(activity)
                    break

        await session.commit()
        await session.refresh(reminder)
        return reminder

    @staticmethod
    async def get_business_reminders(
        session: AsyncSession,
        business_id: int,
        user_id: int | None = None,
    ) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.business), selectinload(Reminder.contact))
            .where(Reminder.business_id == business_id)
        )
        if user_id is not None:
            stmt = stmt.where(Reminder.user_id == user_id)
        stmt = stmt.order_by(asc(Reminder.due_at))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_reminders(
        session: AsyncSession,
        status: str | None = None,
        user_id: int | None = None,
    ) -> list[Reminder]:
        stmt = select(Reminder).options(
            selectinload(Reminder.business), selectinload(Reminder.contact)
        )
        if user_id is not None:
            stmt = stmt.where(Reminder.user_id == user_id)
        if status and status.lower() != "all":
            for st in ReminderStatus:
                if st.value == status.lower():
                    stmt = stmt.where(Reminder.status == st)
                    break
        stmt = stmt.order_by(asc(Reminder.due_at))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_reminder(
        session: AsyncSession,
        reminder_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder:
            raise EntityNotFoundError("Reminder", reminder_id)
        await session.delete(reminder)
        await session.commit()
        logger.info(f"Deleted reminder ID {reminder_id} by user {current_user.email}")
        return {"status": "deleted", "id": reminder_id}

    # ─────────────────────────────────────────────────────────────
    # OUTREACH
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def log_outreach(
        session: AsyncSession,
        business_id: int,
        req: OutreachCreateRequest,
        current_user: User,
    ) -> Outreach:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        channel_enum = OutreachChannel.CALL
        for c in OutreachChannel:
            if c.value.lower() == req.channel.lower():
                channel_enum = c
                break

        status_enum = OutreachStatus.INITIATED
        for st in OutreachStatus:
            if st.value.lower() == (req.status or "initiated").lower():
                status_enum = st
                break

        outreach = Outreach(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.id,
            channel=channel_enum,
            status=status_enum,
            recipient=req.recipient,
            subject=req.subject,
            notes=req.notes,
            metadata_json=req.metadata_json,
            attempted_at=datetime.now(UTC),
        )
        session.add(outreach)

        business.last_outreach_at = datetime.now(UTC)

        act_type_map = {
            OutreachChannel.CALL: ActivityType.CALL_INITIATED,
            OutreachChannel.WHATSAPP: ActivityType.WHATSAPP_OPENED,
            OutreachChannel.EMAIL: ActivityType.EMAIL_INITIATED,
        }
        act_type = act_type_map.get(channel_enum, ActivityType.CALL_INITIATED)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.id,
            contact_id=req.contact_id,
            type=act_type,
            channel=channel_enum.value,
            outcome=f"Outreach {status_enum.value}",
            notes=req.notes or f"{channel_enum.value.capitalize()} attempted to {req.recipient}",
            entity_type="outreach",
            entity_id=outreach.id,
            created_at=datetime.now(UTC),
        )
        session.add(activity)

        await session.commit()
        await session.refresh(outreach)
        return outreach

    @staticmethod
    async def get_business_outreaches(session: AsyncSession, business_id: int) -> list[Outreach]:
        stmt = (
            select(Outreach)
            .where(Outreach.business_id == business_id)
            .order_by(desc(Outreach.attempted_at))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # INTERACTIONS
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def log_interaction(
        session: AsyncSession,
        business_id: int,
        req: InteractionCreateRequest,
        current_user: User,
    ) -> Interaction:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        type_enum = InteractionType.CALL_CONVERSATION
        for t in InteractionType:
            if t.value.lower() == req.type.lower():
                type_enum = t
                break

        interaction = Interaction(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.id,
            outreach_id=req.outreach_id,
            type=type_enum,
            duration_seconds=req.duration_seconds,
            summary=req.summary,
            outcome=req.outcome,
            sentiment=req.sentiment or "neutral",
            occurred_at=datetime.now(UTC),
        )
        session.add(interaction)

        business.last_contacted_at = datetime.now(UTC)

        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()
        if lead and lead.stage == PipelineStage.LEAD:
            lead.stage = PipelineStage.CONTACTED

        activity = Activity(
            business_id=business_id,
            user_id=current_user.id,
            contact_id=req.contact_id,
            type=ActivityType.INTERACTION_LOGGED,
            channel=type_enum.value,
            outcome=req.outcome or "Conversation completed",
            notes=req.summary or "Engagement logged",
            entity_type="interaction",
            entity_id=interaction.id,
            created_at=datetime.now(UTC),
        )
        session.add(activity)

        await session.commit()
        await session.refresh(interaction)
        return interaction

    @staticmethod
    async def get_business_interactions(
        session: AsyncSession, business_id: int
    ) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .where(Interaction.business_id == business_id)
            .order_by(desc(Interaction.occurred_at))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # ACTIVITIES
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_activity(
        session: AsyncSession,
        business_id: int,
        req: ActivityCreateRequest,
        current_user: User,
    ) -> dict[str, Any]:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        act_type = ActivityType.WEBSITE_VISITED
        req_type_str = (req.type or "").lower().strip()
        for member in ActivityType:
            if member.value.lower() == req_type_str or member.name.lower() == req_type_str:
                act_type = member
                break

        activity = Activity(
            business_id=business_id,
            user_id=current_user.id,
            contact_id=req.contact_id,
            type=act_type,
            channel=req.channel or "website",
            outcome=req.outcome,
            notes=req.notes,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            created_at=datetime.now(UTC),
        )
        session.add(activity)
        await session.commit()
        await session.refresh(activity)

        user_name: str | None = current_user.name
        if not user_name and current_user.email:
            user_name = current_user.email.split("@")[0].capitalize()

        return {
            "activity": activity,
            "user_name": user_name,
        }

    @staticmethod
    async def get_business_activities(
        session: AsyncSession,
        business_id: int,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Activity, User)
            .outerjoin(User, Activity.user_id == User.id)
            .where(Activity.business_id == business_id)
            .order_by(desc(Activity.created_at))
        )
        result = await session.execute(stmt)
        rows = result.all()

        enriched = []
        for activity, user in rows:
            user_name: str | None = None
            if user:
                user_name = user.name or (
                    user.email.split("@")[0].capitalize() if user.email else None
                )
            enriched.append(
                {
                    "activity": activity,
                    "user_name": user_name,
                }
            )
        return enriched

    @staticmethod
    async def get_all_activities(
        session: AsyncSession,
        limit: int = 50,
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(Activity, User).outerjoin(User, Activity.user_id == User.id)
        if user_id is not None:
            stmt = stmt.where(Activity.user_id == user_id)
        stmt = stmt.order_by(desc(Activity.created_at)).limit(limit)
        result = await session.execute(stmt)
        rows = result.all()

        enriched = []
        for activity, user in rows:
            user_name: str | None = None
            if user:
                user_name = user.name or (
                    user.email.split("@")[0].capitalize() if user.email else None
                )
            enriched.append(
                {
                    "activity": activity,
                    "user_name": user_name,
                }
            )
        return enriched

    @staticmethod
    async def delete_activity(
        session: AsyncSession,
        activity_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        activity = await session.get(Activity, activity_id)
        if not activity:
            raise EntityNotFoundError("Activity", activity_id)
        await session.delete(activity)
        await session.commit()
        logger.info(f"Deleted activity ID {activity_id} by user {current_user.email}")
        return {"status": "deleted", "id": activity_id}

    # ─────────────────────────────────────────────────────────────
    # CONTACTS
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def list_contacts(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(Contact, Business).outerjoin(Business, Contact.business_id == Business.id)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Contact.first_name.ilike(term),
                    Contact.last_name.ilike(term),
                    Contact.email.ilike(term),
                    Contact.phone.ilike(term),
                    Contact.role.ilike(term),
                    Business.business_name.ilike(term),
                )
            )
        stmt = stmt.order_by(desc(Contact.created_at)).offset(skip).limit(limit)
        result = await session.execute(stmt)
        contacts = []
        for contact, biz in result.all():
            full_name = (
                f"{contact.first_name or ''} {contact.last_name or ''}".strip() or "Unnamed Contact"
            )
            contacts.append(
                {
                    "id": str(contact.id),
                    "name": full_name,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "role": contact.role or "Contact",
                    "email": contact.email,
                    "phone": contact.phone,
                    "business_id": contact.business_id,
                    "company_name": biz.business_name if biz else "Independent",
                    "is_decision_maker": contact.is_decision_maker,
                    "created_at": contact.created_at.isoformat() if contact.created_at else None,
                }
            )
        return contacts

    @staticmethod
    async def delete_contact(
        session: AsyncSession,
        contact_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        contact = await session.get(Contact, contact_id)
        if not contact:
            raise EntityNotFoundError("Contact", contact_id)

        # Unlink foreign keys safely
        await session.execute(
            update(Note).where(Note.contact_id == contact_id).values(contact_id=None)
        )
        await session.execute(
            update(Task).where(Task.contact_id == contact_id).values(contact_id=None)
        )
        await session.execute(
            update(Reminder).where(Reminder.contact_id == contact_id).values(contact_id=None)
        )
        await session.execute(
            update(Outreach).where(Outreach.contact_id == contact_id).values(contact_id=None)
        )
        await session.execute(
            update(Interaction).where(Interaction.contact_id == contact_id).values(contact_id=None)
        )
        await session.execute(
            update(Activity).where(Activity.contact_id == contact_id).values(contact_id=None)
        )

        await session.delete(contact)
        await session.commit()
        logger.info(f"Deleted contact ID {contact_id} by user {current_user.email}")
        return {"status": "deleted", "id": contact_id}


class ReminderNotificationService:
    """Service responsible for checking due sales reminders and dispatching push notifications."""

    @classmethod
    async def process_due_reminders(cls, session: AsyncSession) -> int:
        now = datetime.now(UTC)

        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.business), selectinload(Reminder.user))
            .where(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.due_at <= now,
                Reminder.notification_sent_at.is_(None),
            )
            .order_by(Reminder.due_at.asc())
            .limit(50)
        )
        result = await session.execute(stmt)
        due_reminders: list[Reminder] = list(result.scalars().all())

        if not due_reminders:
            return 0

        logger.info(f"Found {len(due_reminders)} due reminders to notify.")
        processed_count = 0

        for reminder in due_reminders:
            user_id = reminder.user_id
            biz_name = reminder.business.business_name if reminder.business else "FastUI Sales"

            sub_stmt = select(PushSubscription)
            if user_id:
                sub_stmt = sub_stmt.where(PushSubscription.user_id == user_id)

            sub_res = await session.execute(sub_stmt)
            subscriptions = list(sub_res.scalars().all())

            payload = {
                "title": f"Reminder: {biz_name}",
                "body": reminder.title + (f" · {reminder.notes}" if reminder.notes else ""),
                "icon": "/assets/brand/icon/monochrome/white/solid.png",
                "badge": "/assets/brand/notification/badge/monochrome/white/solid.png",
                "data": {
                    "url": "/prospects",
                    "business_id": reminder.business_id,
                    "reminder_id": reminder.id,
                },
            }

            for sub in subscriptions:
                sub_info = {
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                }
                success = await NotificationService.send_notification(
                    sub_info,
                    payload,
                )
                if not success:
                    # Stale / expired subscription — clean up
                    await session.delete(sub)

            reminder.notification_sent_at = datetime.now(UTC)
            processed_count += 1

        await session.commit()
        return processed_count
