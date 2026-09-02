import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, asc
from sqlalchemy.orm import selectinload

from core.exceptions import EntityNotFoundException
from models.schema import (
    Business, Lead, Contact, Note, Task, Reminder,
    Outreach, Interaction, Activity, User,
    PipelineStage, LeadPriority, LeadSignal,
    OutreachChannel, OutreachStatus, InteractionType,
    ActivityType, TaskStatus, ReminderStatus
)
from schemas.businesses import (
    StageUpdateResponse, BusinessResponse, BusinessUpdateRequest,
    OutreachCreateRequest, InteractionCreateRequest,
    NoteCreateRequest, TaskCreateRequest, TaskUpdateRequest,
    ReminderCreateRequest, ReminderUpdateRequest,
    BulkAddToLeadsResponse, BulkDeleteResponse, PipelineDealResponse
)
from schemas.auth import TokenData

logger = logging.getLogger(__name__)

class BusinessService:
    # ─────────────────────────────────────────────────────────────
    # PROSPECTS (Discovered businesses not yet promoted to Leads)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_prospects(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        qualification_status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[BusinessResponse]:
        """
        Fetches businesses that have NOT been converted to active sales leads (Lead is NULL).
        """
        query = (
            select(Business, Lead)
            .outerjoin(Lead, Business.id == Lead.business_id)
            .where(Lead.id.is_(None))
        )

        # Qualification filter
        if qualification_status and qualification_status.lower() != "all":
            query = query.where(Business.qualification_status == qualification_status.lower())

        # Multi-field search
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Business.business_name.ilike(term),
                    Business.category.ilike(term),
                    Business.city.ilike(term),
                    Business.state.ilike(term),
                    Business.country.ilike(term),
                    Business.website.ilike(term),
                    Business.phone.ilike(term),
                )
            )

        # Sorting
        sort_columns = {
            "created_at": Business.created_at,
            "business_name": Business.business_name,
            "city": Business.city,
            "qualification_status": Business.qualification_status
        }
        col = sort_columns.get(sort_by, Business.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(col), asc(Business.id))
        else:
            query = query.order_by(desc(col), desc(Business.id))

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        rows = result.all()

        responses = []
        for business, lead in rows:
            responses.append(
                BusinessResponse(
                    id=business.id,
                    business_name=business.business_name,
                    category=business.category,
                    phone=business.phone,
                    email=business.email,
                    website=business.website,
                    has_whatsapp=business.has_whatsapp,
                    address=business.address,
                    city=business.city,
                    state=business.state,
                    country=business.country,
                    postal_code=business.postal_code,
                    website_status=business.website_status.value if hasattr(business.website_status, 'value') else str(business.website_status),
                    qualification_status=business.qualification_status or "unqualified",
                    is_lead=False,
                    pipeline_stage=None,
                    stage=None,
                    priority="medium",
                    signal="warm",
                    score=50,
                    lead_id=None,
                    last_outreach_at=business.last_outreach_at.isoformat() if business.last_outreach_at else None,
                    last_contacted_at=business.last_contacted_at.isoformat() if business.last_contacted_at else None,
                    created_at=business.created_at.isoformat() if business.created_at else None,
                    updated_at=business.updated_at.isoformat() if business.updated_at else None,
                )
            )

        return responses

    @staticmethod
    async def add_to_leads(
        session: AsyncSession,
        business_id: int,
        current_user: TokenData
    ) -> BusinessResponse:
        """
        Promotes a prospect to active sales Lead and creates its Lead record.
        """
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        # Check if already a lead
        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()

        if not lead:
            lead = Lead(
                business_id=business_id,
                owner_id=current_user.user_id,
                stage=PipelineStage.LEAD,
                priority=LeadPriority.MEDIUM,
                signal=LeadSignal.WARM,
                score=50,
                source="prospect"
            )
            session.add(lead)
            await session.flush()

            # Mark business as qualified
            business.qualification_status = "qualified"

            activity = Activity(
                business_id=business.id,
                user_id=current_user.user_id,
                type=ActivityType.LEAD_CREATED,
                channel="crm",
                outcome="Added to Leads",
                notes="Promoted from Prospect into active Sales pipeline",
                entity_type="lead",
                entity_id=lead.id
            )
            session.add(activity)
            await session.commit()
            await session.refresh(lead)

        return await BusinessService.get_business_by_id(session=session, business_id=business_id)

    @staticmethod
    async def bulk_add_to_leads(
        session: AsyncSession,
        business_ids: List[int],
        current_user: TokenData
    ) -> BulkAddToLeadsResponse:
        """
        Bulk promotes multiple selected prospects to Leads.
        """
        if not business_ids:
            return BulkAddToLeadsResponse(message="No business IDs provided", added_count=0, business_ids=[])

        added_ids = []
        for b_id in business_ids:
            business = await session.get(Business, b_id)
            if not business:
                continue

            lead_res = await session.execute(select(Lead).where(Lead.business_id == b_id))
            lead = lead_res.scalar_one_or_none()
            if not lead:
                lead = Lead(
                    business_id=b_id,
                    owner_id=current_user.user_id,
                    stage=PipelineStage.LEAD,
                    priority=LeadPriority.MEDIUM,
                    signal=LeadSignal.WARM,
                    score=50,
                    source="prospect"
                )
                session.add(lead)
                await session.flush()

                business.qualification_status = "qualified"

                activity = Activity(
                    business_id=business.id,
                    user_id=current_user.user_id,
                    type=ActivityType.LEAD_CREATED,
                    channel="crm",
                    outcome="Added to Leads",
                    notes="Promoted from Prospect into active Sales pipeline via bulk action",
                    entity_type="lead",
                    entity_id=lead.id
                )
                session.add(activity)
                added_ids.append(b_id)

        await session.commit()
        return BulkAddToLeadsResponse(
            message=f"Successfully added {len(added_ids)} prospects to Leads",
            added_count=len(added_ids),
            business_ids=added_ids
        )

    @staticmethod
    async def qualify_prospect(
        session: AsyncSession,
        business_id: int,
        qualification_status: str,
        current_user: TokenData
    ) -> BusinessResponse:
        """
        Updates prospect qualification status.
        """
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        old_status = business.qualification_status
        business.qualification_status = qualification_status.lower()

        activity = Activity(
            business_id=business.id,
            user_id=current_user.user_id,
            type=ActivityType.STATUS_CHANGED,
            channel="crm",
            outcome=f"Qualification updated to {qualification_status}",
            notes=f"Prospect qualification changed from '{old_status}' to '{qualification_status}'",
            entity_type="business",
            entity_id=business.id
        )
        session.add(activity)
        await session.commit()

        return await BusinessService.get_business_by_id(session=session, business_id=business_id)

    # ─────────────────────────────────────────────────────────────
    # LEADS (Businesses in active sales pipeline)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_businesses(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        stage: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[BusinessResponse]:
        """
        Fetches businesses that HAVE an active sales Lead record.
        """
        query = (
            select(Business, Lead)
            .join(Lead, Business.id == Lead.business_id)
        )

        # Stage filter (on Lead.stage)
        if stage and stage.lower() != "all":
            stage_enum = None
            for s in PipelineStage:
                if s.value.lower() == stage.lower() or s.name.lower() == stage.lower():
                    stage_enum = s
                    break
            if stage_enum:
                query = query.where(Lead.stage == stage_enum)

        # Multi-field search
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Business.business_name.ilike(term),
                    Business.category.ilike(term),
                    Business.city.ilike(term),
                    Business.state.ilike(term),
                    Business.country.ilike(term),
                    Business.website.ilike(term),
                    Business.phone.ilike(term),
                )
            )

        # Sorting
        sort_columns = {
            "created_at": Business.created_at,
            "business_name": Business.business_name,
            "city": Business.city,
            "stage": Lead.stage,
            "pipeline_stage": Lead.stage
        }
        col = sort_columns.get(sort_by, Business.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(col), asc(Business.id))
        else:
            query = query.order_by(desc(col), desc(Business.id))

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        rows = result.all()

        responses = []
        for business, lead in rows:
            lead_stage = lead.stage.value if lead and hasattr(lead.stage, 'value') else (str(lead.stage) if lead else "lead")
            lead_priority = lead.priority.value if lead and hasattr(lead.priority, 'value') else "medium"
            lead_signal = lead.signal.value if lead and hasattr(lead.signal, 'value') else "warm"
            lead_score = lead.score if lead else 50
            lead_id = lead.id if lead else None

            responses.append(
                BusinessResponse(
                    id=business.id,
                    business_name=business.business_name,
                    category=business.category,
                    phone=business.phone,
                    email=business.email,
                    website=business.website,
                    has_whatsapp=business.has_whatsapp,
                    address=business.address,
                    city=business.city,
                    state=business.state,
                    country=business.country,
                    postal_code=business.postal_code,
                    website_status=business.website_status.value if hasattr(business.website_status, 'value') else str(business.website_status),
                    qualification_status=business.qualification_status or "qualified",
                    is_lead=True,
                    pipeline_stage=lead_stage,
                    stage=lead_stage,
                    priority=lead_priority,
                    signal=lead_signal,
                    score=lead_score,
                    lead_id=lead_id,
                    last_outreach_at=business.last_outreach_at.isoformat() if business.last_outreach_at else None,
                    last_contacted_at=business.last_contacted_at.isoformat() if business.last_contacted_at else None,
                    created_at=business.created_at.isoformat() if business.created_at else None,
                    updated_at=business.updated_at.isoformat() if business.updated_at else None,
                )
            )

        return responses

    @staticmethod
    async def get_business_by_id(session: AsyncSession, business_id: int) -> BusinessResponse:
        query = (
            select(Business, Lead)
            .outerjoin(Lead, Business.id == Lead.business_id)
            .where(Business.id == business_id)
        )
        result = await session.execute(query)
        row = result.first()
        if not row:
            raise EntityNotFoundException("Business", business_id)

        business, lead = row
        lead_stage = lead.stage.value if lead and hasattr(lead.stage, 'value') else (str(lead.stage) if lead else None)
        lead_priority = lead.priority.value if lead and hasattr(lead.priority, 'value') else "medium"
        lead_signal = lead.signal.value if lead and hasattr(lead.signal, 'value') else "warm"
        lead_score = lead.score if lead else 50
        lead_id = lead.id if lead else None
        is_lead = lead is not None

        return BusinessResponse(
            id=business.id,
            business_name=business.business_name,
            category=business.category,
            phone=business.phone,
            email=business.email,
            website=business.website,
            has_whatsapp=business.has_whatsapp,
            address=business.address,
            city=business.city,
            state=business.state,
            country=business.country,
            postal_code=business.postal_code,
            website_status=business.website_status.value if hasattr(business.website_status, 'value') else str(business.website_status),
            qualification_status=business.qualification_status or "unqualified",
            is_lead=is_lead,
            pipeline_stage=lead_stage,
            stage=lead_stage,
            priority=lead_priority,
            signal=lead_signal,
            score=lead_score,
            lead_id=lead_id,
            last_outreach_at=business.last_outreach_at.isoformat() if business.last_outreach_at else None,
            last_contacted_at=business.last_contacted_at.isoformat() if business.last_contacted_at else None,
            created_at=business.created_at.isoformat() if business.created_at else None,
            updated_at=business.updated_at.isoformat() if business.updated_at else None,
        )

    @staticmethod
    async def update_pipeline_stage(
        session: AsyncSession,
        business_id: int,
        new_stage: str,
        current_user: TokenData
    ) -> StageUpdateResponse:
        """
        Updates pipeline stage on Lead for a business and records an audit activity.
        """
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        # Fetch or create lead record
        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()

        stage_enum = None
        for s in PipelineStage:
            if s.value.lower() == new_stage.lower():
                stage_enum = s
                break
        if not stage_enum:
            stage_enum = PipelineStage.LEAD

        old_stage = "lead"
        if not lead:
            lead = Lead(
                business_id=business_id,
                owner_id=current_user.user_id,
                stage=stage_enum
            )
            session.add(lead)
        else:
            old_stage = lead.stage.value if hasattr(lead.stage, 'value') else str(lead.stage)
            lead.stage = stage_enum

        audit_activity = Activity(
            business_id=business.id,
            user_id=current_user.user_id,
            type=ActivityType.STATUS_CHANGED,
            channel="crm",
            outcome=f"Stage updated to {stage_enum.value}",
            notes=f"Pipeline stage moved from '{old_stage}' to '{stage_enum.value}'",
            entity_type="lead",
            entity_id=lead.id if lead else None
        )
        session.add(audit_activity)
        await session.commit()

        logger.info(f"Business {business_id} stage updated: {old_stage} -> {stage_enum.value} by {current_user.email}")

        return StageUpdateResponse(
            message="Stage updated successfully",
            business_id=business_id,
            old_stage=old_stage,
            new_stage=stage_enum.value
        )

    # ─────────────────────────────────────────────────────────────
    # OUTREACH (What we attempted)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def log_outreach(
        session: AsyncSession,
        business_id: int,
        req: OutreachCreateRequest,
        current_user: TokenData
    ) -> Outreach:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

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
            user_id=current_user.user_id,
            channel=channel_enum,
            status=status_enum,
            recipient=req.recipient,
            subject=req.subject,
            notes=req.notes,
            metadata_json=req.metadata_json,
            attempted_at=datetime.now(timezone.utc)
        )
        session.add(outreach)

        # Update last_outreach_at on master Business record
        business.last_outreach_at = datetime.now(timezone.utc)

        # Map channel to ActivityType
        act_type_map = {
            OutreachChannel.CALL: ActivityType.CALL_INITIATED,
            OutreachChannel.WHATSAPP: ActivityType.WHATSAPP_OPENED,
            OutreachChannel.EMAIL: ActivityType.EMAIL_INITIATED,
        }
        act_type = act_type_map.get(channel_enum, ActivityType.CALL_INITIATED)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.user_id,
            contact_id=req.contact_id,
            type=act_type,
            channel=channel_enum.value,
            outcome=f"Outreach {status_enum.value}",
            notes=req.notes or f"{channel_enum.value.capitalize()} attempted to {req.recipient}",
            entity_type="outreach",
            entity_id=outreach.id
        )
        session.add(activity)

        await session.commit()
        await session.refresh(outreach)
        return outreach

    @staticmethod
    async def get_business_outreaches(session: AsyncSession, business_id: int) -> List[Outreach]:
        query = select(Outreach).where(Outreach.business_id == business_id).order_by(desc(Outreach.attempted_at))
        result = await session.execute(query)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # INTERACTION (Actual conversation / engagement)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def log_interaction(
        session: AsyncSession,
        business_id: int,
        req: InteractionCreateRequest,
        current_user: TokenData
    ) -> Interaction:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        type_enum = InteractionType.CALL_CONVERSATION
        for t in InteractionType:
            if t.value.lower() == req.type.lower():
                type_enum = t
                break

        interaction = Interaction(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.user_id,
            outreach_id=req.outreach_id,
            type=type_enum,
            duration_seconds=req.duration_seconds,
            summary=req.summary,
            outcome=req.outcome,
            sentiment=req.sentiment or "neutral",
            occurred_at=datetime.now(timezone.utc)
        )
        session.add(interaction)

        # Verified conversation -> updates last_contacted_at
        business.last_contacted_at = datetime.now(timezone.utc)

        # Auto-advance stage from lead to contacted if applicable
        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()
        if lead and lead.stage == PipelineStage.LEAD:
            lead.stage = PipelineStage.CONTACTED

        activity = Activity(
            business_id=business_id,
            user_id=current_user.user_id,
            contact_id=req.contact_id,
            type=ActivityType.INTERACTION_LOGGED,
            channel=type_enum.value,
            outcome=req.outcome or "Conversation completed",
            notes=req.summary or "Engagement logged",
            entity_type="interaction",
            entity_id=interaction.id
        )
        session.add(activity)

        await session.commit()
        await session.refresh(interaction)
        return interaction

    @staticmethod
    async def get_business_interactions(session: AsyncSession, business_id: int) -> List[Interaction]:
        query = select(Interaction).where(Interaction.business_id == business_id).order_by(desc(Interaction.occurred_at))
        result = await session.execute(query)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # NOTE (Dedicated User Notes)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_note(
        session: AsyncSession,
        business_id: int,
        req: NoteCreateRequest,
        current_user: TokenData
    ) -> Note:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        note = Note(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.user_id,
            content=req.content
        )
        session.add(note)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.user_id,
            contact_id=req.contact_id,
            type=ActivityType.NOTE_ADDED,
            channel="note",
            outcome="Note added",
            notes=req.content,
            entity_type="note",
            entity_id=note.id
        )
        session.add(activity)

        await session.commit()
        await session.refresh(note)
        return note

    @staticmethod
    async def get_business_notes(session: AsyncSession, business_id: int) -> List[Note]:
        query = select(Note).where(Note.business_id == business_id).order_by(desc(Note.created_at))
        result = await session.execute(query)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # TASK (Work that needs to be done)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_task(
        session: AsyncSession,
        business_id: int,
        req: TaskCreateRequest,
        current_user: TokenData
    ) -> Task:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        task = Task(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.user_id,
            title=req.title,
            description=req.description,
            priority=LeadPriority(req.priority.lower()) if req.priority and req.priority.lower() in [p.value for p in LeadPriority] else LeadPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=req.due_date if isinstance(req.due_date, datetime) else None
        )
        session.add(task)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.user_id,
            contact_id=req.contact_id,
            type=ActivityType.TASK_CREATED,
            channel="task",
            outcome="Task created",
            notes=req.title,
            entity_type="task",
            entity_id=task.id
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
        current_user: TokenData
    ) -> Task:
        task = await session.get(Task, task_id)
        if not task:
            raise EntityNotFoundException("Task", task_id)

        if req.title is not None:
            task.title = req.title
        if req.description is not None:
            task.description = req.description
        if req.priority is not None:
            for p in LeadPriority:
                if p.value == req.priority.lower():
                    task.priority = p
                    break
        if req.status is not None:
            for st in TaskStatus:
                if st.value == req.status.lower():
                    task.status = st
                    if st == TaskStatus.COMPLETED:
                        task.completed_at = datetime.now(timezone.utc)
                        activity = Activity(
                            business_id=task.business_id,
                            user_id=current_user.user_id,
                            contact_id=task.contact_id,
                            type=ActivityType.TASK_COMPLETED,
                            channel="task",
                            outcome="Task completed",
                            notes=task.title,
                            entity_type="task",
                            entity_id=task.id
                        )
                        session.add(activity)
                    break

        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def get_all_tasks(
        session: AsyncSession,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Task]:
        """Returns tasks scoped to the authenticated user."""
        query = select(Task)
        # Scope to current user — never leak cross-user tasks
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        if status and status.lower() != "all":
            for st in TaskStatus:
                if st.value == status.lower():
                    query = query.where(Task.status == st)
                    break
        query = query.order_by(asc(Task.due_date))
        result = await session.execute(query)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # REMINDER (When user should be reminded)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def create_reminder(
        session: AsyncSession,
        business_id: int,
        req: ReminderCreateRequest,
        current_user: TokenData
    ) -> Reminder:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        # Strict UTC normalization
        if isinstance(req.due_at, datetime):
            if req.due_at.tzinfo is None:
                due_at_dt = req.due_at.replace(tzinfo=timezone.utc)
            else:
                due_at_dt = req.due_at.astimezone(timezone.utc)
        elif isinstance(req.due_at, str):
            try:
                raw_str = req.due_at.strip().replace("Z", "+00:00")
                parsed_dt = datetime.fromisoformat(raw_str)
                if parsed_dt.tzinfo is None:
                    due_at_dt = parsed_dt.replace(tzinfo=timezone.utc)
                else:
                    due_at_dt = parsed_dt.astimezone(timezone.utc)
            except Exception:
                due_at_dt = datetime.now(timezone.utc)
        else:
            due_at_dt = datetime.now(timezone.utc)

        reminder = Reminder(
            business_id=business_id,
            contact_id=req.contact_id,
            user_id=current_user.user_id,
            task_id=req.task_id,
            title=req.title,
            notes=req.notes,
            due_at=due_at_dt,
            status=ReminderStatus.PENDING
        )
        session.add(reminder)

        activity = Activity(
            business_id=business_id,
            user_id=current_user.user_id,
            contact_id=req.contact_id,
            type=ActivityType.REMINDER_CREATED,
            channel="reminder",
            outcome="Reminder scheduled",
            notes=f"{req.title} - due {due_at_dt.strftime('%b %d, %I:%M %p')}",
            entity_type="reminder",
            entity_id=reminder.id
        )
        session.add(activity)

        await session.commit()
        await session.refresh(reminder)
        return reminder

    @staticmethod
    async def update_reminder(
        session: AsyncSession,
        reminder_id: int,
        req: ReminderUpdateRequest,
        current_user: TokenData
    ) -> Reminder:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder:
            raise EntityNotFoundException("Reminder", reminder_id)

        if req.title is not None:
            reminder.title = req.title
        if req.notes is not None:
            reminder.notes = req.notes
        if req.due_at is not None:
            if isinstance(req.due_at, datetime):
                if req.due_at.tzinfo is None:
                    reminder.due_at = req.due_at.replace(tzinfo=timezone.utc)
                else:
                    reminder.due_at = req.due_at.astimezone(timezone.utc)
            elif isinstance(req.due_at, str):
                try:
                    raw_str = req.due_at.strip().replace("Z", "+00:00")
                    parsed_dt = datetime.fromisoformat(raw_str)
                    if parsed_dt.tzinfo is None:
                        reminder.due_at = parsed_dt.replace(tzinfo=timezone.utc)
                    else:
                        reminder.due_at = parsed_dt.astimezone(timezone.utc)
                except Exception:
                    pass
        if req.status is not None:
            for st in ReminderStatus:
                if st.value == req.status.lower():
                    reminder.status = st
                    if st == ReminderStatus.COMPLETED:
                        reminder.completed_at = datetime.now(timezone.utc)
                        activity = Activity(
                            business_id=reminder.business_id,
                            user_id=current_user.user_id,
                            contact_id=reminder.contact_id,
                            type=ActivityType.REMINDER_COMPLETED,
                            channel="reminder",
                            outcome="Reminder completed",
                            notes=reminder.title,
                            entity_type="reminder",
                            entity_id=reminder.id
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
        user_id: Optional[int] = None
    ) -> List[Reminder]:
        """Returns reminders for a specific business, ordered by due_at ascending."""
        query = (
            select(Reminder)
            .options(selectinload(Reminder.business), selectinload(Reminder.contact))
            .where(Reminder.business_id == business_id)
        )
        if user_id is not None:
            query = query.where(Reminder.user_id == user_id)
        query = query.order_by(asc(Reminder.due_at))
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_reminders(
        session: AsyncSession,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Reminder]:
        """Returns reminders scoped to the authenticated user."""
        query = (
            select(Reminder)
            .options(selectinload(Reminder.business), selectinload(Reminder.contact))
        )
        # Scope to current user — never leak cross-user reminders
        if user_id is not None:
            query = query.where(Reminder.user_id == user_id)
        if status and status.lower() != "all":
            for st in ReminderStatus:
                if st.value == status.lower():
                    query = query.where(Reminder.status == st)
                    break
        query = query.order_by(asc(Reminder.due_at))
        result = await session.execute(query)
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────
    # ACTIVITY (Timeline audit stream)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_business_activities(
        session: AsyncSession,
        business_id: int
    ) -> List[Dict[str, Any]]:
        """
        Returns activities for a business, joined with User to provide
        the actor's display name (user_name) for correct frontend attribution.
        """
        query = (
            select(Activity, User)
            .outerjoin(User, Activity.user_id == User.id)
            .where(Activity.business_id == business_id)
            .order_by(desc(Activity.created_at))
        )
        result = await session.execute(query)
        rows = result.all()

        enriched = []
        for activity, user in rows:
            # Derive a display-ready name: full name first, then email prefix, then None
            user_name: Optional[str] = None
            if user:
                if user.name:
                    user_name = user.name
                elif user.email:
                    user_name = user.email.split("@")[0].capitalize()
            enriched.append({
                "activity": activity,
                "user_name": user_name,
            })
        return enriched

    @staticmethod
    async def get_all_activities(
        session: AsyncSession,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns global activities enriched with actor name.
        When user_id is provided, scopes results to that user.
        """
        query = (
            select(Activity, User)
            .outerjoin(User, Activity.user_id == User.id)
        )
        # Scope to authenticated user when provided
        if user_id is not None:
            query = query.where(Activity.user_id == user_id)
        query = query.order_by(desc(Activity.created_at)).limit(limit)
        result = await session.execute(query)
        rows = result.all()

        enriched = []
        for activity, user in rows:
            user_name: Optional[str] = None
            if user:
                if user.name:
                    user_name = user.name
                elif user.email:
                    user_name = user.email.split("@")[0].capitalize()
            enriched.append({
                "activity": activity,
                "user_name": user_name,
            })
        return enriched

    @staticmethod
    async def update_business(
        session: AsyncSession,
        business_id: int,
        req: BusinessUpdateRequest,
        current_user: TokenData
    ) -> BusinessResponse:
        """
        Updates business and associated lead details and records changes to database.
        """
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        if req.business_name is not None:
            business.business_name = req.business_name.strip()
        if req.category is not None:
            business.category = req.category.strip()
        if req.phone is not None:
            business.phone = req.phone.strip()
            business.has_whatsapp = bool(business.phone)
        if req.email is not None:
            business.email = req.email.strip()
        if req.website is not None:
            business.website = req.website.strip()
        if req.address is not None:
            business.address = req.address.strip()
        if req.city is not None:
            business.city = req.city.strip()
        if req.state is not None:
            business.state = req.state.strip()
        if req.country is not None:
            business.country = req.country.strip()
        if req.postal_code is not None:
            business.postal_code = req.postal_code.strip()
        if req.qualification_status is not None:
            business.qualification_status = req.qualification_status.lower()

        # Check for associated lead to update lead-specific fields
        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()

        if lead:
            if req.stage is not None:
                for s in PipelineStage:
                    if s.value.lower() == req.stage.lower():
                        lead.stage = s
                        break
            if req.priority is not None:
                for p in LeadPriority:
                    if p.value.lower() == req.priority.lower():
                        lead.priority = p
                        break
            if req.signal is not None:
                for sg in LeadSignal:
                    if sg.value.lower() == req.signal.lower():
                        lead.signal = sg
                        break
            if req.score is not None:
                lead.score = req.score

        activity = Activity(
            business_id=business.id,
            user_id=current_user.user_id,
            type=ActivityType.INTERACTION_LOGGED,
            channel="crm",
            outcome="Record updated",
            notes=f"Updated details for {business.business_name}",
            entity_type="business",
            entity_id=business.id
        )
        session.add(activity)

        await session.commit()
        await session.refresh(business)
        return await BusinessService.get_business_by_id(session=session, business_id=business_id)

    @staticmethod
    async def delete_business(
        session: AsyncSession,
        business_id: int,
        current_user: TokenData
    ) -> Dict[str, Any]:
        """
        Deletes a business record and all related cascade entities (leads, notes, tasks, reminders, activities).
        """
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundException("Business", business_id)

        name = business.business_name
        await session.delete(business)
        await session.commit()
        logger.info(f"Deleted business ID {business_id} ('{name}') by user {current_user.email}")
        return {"status": "deleted", "id": business_id, "name": name}

    @staticmethod
    async def bulk_delete_businesses(
        session: AsyncSession,
        business_ids: List[int],
        current_user: TokenData
    ) -> BulkDeleteResponse:
        """
        Bulk deletes multiple business records.
        """
        if not business_ids:
            return BulkDeleteResponse(message="No business IDs provided", deleted_count=0, business_ids=[])

        deleted_ids = []
        for b_id in business_ids:
            business = await session.get(Business, b_id)
            if business:
                await session.delete(business)
                deleted_ids.append(b_id)

        await session.commit()
        logger.info(f"Bulk deleted {len(deleted_ids)} businesses by user {current_user.email}")
        return BulkDeleteResponse(
            message=f"Successfully deleted {len(deleted_ids)} records",
            deleted_count=len(deleted_ids),
            business_ids=deleted_ids
        )

    @staticmethod
    async def delete_note(
        session: AsyncSession,
        note_id: int,
        current_user: TokenData
    ) -> Dict[str, Any]:
        note = await session.get(Note, note_id)
        if not note:
            raise EntityNotFoundException("Note", note_id)
        await session.delete(note)
        await session.commit()
        return {"status": "deleted", "id": note_id}

    @staticmethod
    async def delete_task(
        session: AsyncSession,
        task_id: int,
        current_user: TokenData
    ) -> Dict[str, Any]:
        task = await session.get(Task, task_id)
        if not task:
            raise EntityNotFoundException("Task", task_id)
        await session.delete(task)
        await session.commit()
        return {"status": "deleted", "id": task_id}

    @staticmethod
    async def delete_reminder(
        session: AsyncSession,
        reminder_id: int,
        current_user: TokenData
    ) -> Dict[str, Any]:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder:
            raise EntityNotFoundException("Reminder", reminder_id)
        await session.delete(reminder)
        await session.commit()
        return {"status": "deleted", "id": reminder_id}

    @staticmethod
    async def get_pipeline_deals(
        session: AsyncSession,
        current_user: TokenData
    ) -> List[Dict[str, Any]]:
        """
        Returns all active pipeline leads formatted for the Pipeline board view.
        """
        query = (
            select(Business, Lead)
            .join(Lead, Business.id == Lead.business_id)
            .order_by(desc(Lead.updated_at))
        )
        result = await session.execute(query)
        rows = result.all()

        stage_map = {
            "lead": "Qualification",
            "contacted": "Demo",
            "qualified": "Demo",
            "proposal": "Proposal",
            "won": "Closed Won",
            "lost": "Qualification"
        }

        probability_map = {
            "lead": 20,
            "contacted": 40,
            "qualified": 60,
            "proposal": 80,
            "won": 100,
            "lost": 0
        }

        deals = []
        for business, lead in rows:
            raw_stage = lead.stage.value if hasattr(lead.stage, 'value') else str(lead.stage).lower()
            board_stage = stage_map.get(raw_stage, "Qualification")
            deals.append({
                "id": str(business.id),
                "business_name": business.business_name,
                "stage": board_stage,
                "value": (lead.score or 50) * 100,
                "probability": probability_map.get(raw_stage, 50),
                "priority": lead.priority.value if hasattr(lead.priority, 'value') else str(lead.priority),
                "lead_id": lead.id,
                "city": business.city,
                "category": business.category
            })
        return deals
