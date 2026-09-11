"""FastUI Lead Domain Service.

Manages sales pipeline promotion, stage updates, scoring, and lead assignment.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import asc, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.mapping import map_business_response
from app.domains.businesses.models import Business, BusinessSource
from app.domains.businesses.schemas import BusinessResponse
from app.domains.engagement.models import Activity, ActivityType
from app.domains.leads.models import Lead, LeadPriority, LeadSignal, PipelineStage
from app.domains.leads.schemas import (
    BulkAddToLeadsResponse,
    StageUpdateResponse,
)
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class LeadService:
    """Service managing sales lead promotions, pipeline stage updates, and qualifications."""

    @staticmethod
    async def list_leads(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        stage: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[BusinessResponse]:
        """Fetches all businesses that have an active sales Lead record."""
        query = select(Business, Lead).join(Lead, Business.id == Lead.business_id)

        if stage and stage.lower() != "all":
            for s in PipelineStage:
                if s.value.lower() == stage.lower() or s.name.lower() == stage.lower():
                    query = query.where(Lead.stage == s)
                    break

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

        sort_columns = {
            "created_at": Business.created_at,
            "business_name": Business.business_name,
            "city": Business.city,
            "stage": Lead.stage,
            "pipeline_stage": Lead.stage,
        }
        col = sort_columns.get(sort_by, Business.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(col), asc(Business.id))
        else:
            query = query.order_by(desc(col), desc(Business.id))

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        rows = result.all()

        business_ids = [business.id for business, _ in rows]
        sources_by_biz: dict[int, BusinessSource] = {}
        if business_ids:
            src_stmt = select(BusinessSource).where(
                BusinessSource.business_id.in_(business_ids),
                BusinessSource.platform == "google_maps",
            )
            src_res = await session.execute(src_stmt)
            for s in src_res.scalars().all():
                sources_by_biz[s.business_id] = s

        return [
            map_business_response(business, lead, sources_by_biz.get(business.id))
            for business, lead in rows
        ]

    @staticmethod
    async def promote_to_lead(
        session: AsyncSession,
        business_id: int,
        user_id: int | None = None,
    ) -> BusinessResponse:
        """Promotes a prospect to an active sales Lead record."""
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()

        if not lead:
            lead = Lead(
                business_id=business_id,
                owner_id=user_id,
                stage=PipelineStage.LEAD,
                priority=LeadPriority.MEDIUM,
                signal=LeadSignal.WARM,
                score=50,
                source="prospect",
            )
            session.add(lead)
            await session.flush()

            business.qualification_status = "qualified"

            activity = Activity(
                business_id=business.id,
                user_id=user_id,
                type=ActivityType.LEAD_CREATED,
                channel="crm",
                outcome="Added to Leads",
                notes="Promoted from Prospect into active Sales pipeline",
                entity_type="lead",
                entity_id=lead.id,
            )
            session.add(activity)
            await session.commit()
            await session.refresh(lead)

        from app.domains.businesses.service import BusinessService

        return await BusinessService.get_business_by_id(session=session, business_id=business_id)

    @staticmethod
    async def bulk_promote_to_leads(
        session: AsyncSession,
        business_ids: list[int],
        user_id: int | None = None,
    ) -> BulkAddToLeadsResponse:
        """Bulk promotes multiple prospects to Leads."""
        if not business_ids:
            return BulkAddToLeadsResponse(
                message="No business IDs provided", added_count=0, business_ids=[]
            )

        added_ids: list[int] = []
        for b_id in business_ids:
            business = await session.get(Business, b_id)
            if not business:
                continue

            lead_res = await session.execute(select(Lead).where(Lead.business_id == b_id))
            lead = lead_res.scalar_one_or_none()
            if not lead:
                lead = Lead(
                    business_id=b_id,
                    owner_id=user_id,
                    stage=PipelineStage.LEAD,
                    priority=LeadPriority.MEDIUM,
                    signal=LeadSignal.WARM,
                    score=50,
                    source="prospect",
                )
                session.add(lead)
                await session.flush()

                business.qualification_status = "qualified"

                activity = Activity(
                    business_id=business.id,
                    user_id=user_id,
                    type=ActivityType.LEAD_CREATED,
                    channel="crm",
                    outcome="Added to Leads",
                    notes="Promoted from Prospect into active Sales pipeline via bulk action",
                    entity_type="lead",
                    entity_id=lead.id,
                )
                session.add(activity)
                added_ids.append(b_id)

        await session.commit()
        return BulkAddToLeadsResponse(
            message=f"Successfully added {len(added_ids)} prospects to Leads",
            added_count=len(added_ids),
            business_ids=added_ids,
        )

    @staticmethod
    async def update_stage(
        session: AsyncSession,
        business_id: int,
        new_stage: str,
        user_id: int | None = None,
    ) -> StageUpdateResponse:
        """Updates pipeline stage on Lead and records audit activity."""
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        lead_res = await session.execute(select(Lead).where(Lead.business_id == business_id))
        lead = lead_res.scalar_one_or_none()

        stage_enum = PipelineStage.LEAD
        for s in PipelineStage:
            if s.value.lower() == new_stage.lower() or s.name.lower() == new_stage.lower():
                stage_enum = s
                break

        old_stage = "lead"
        if not lead:
            lead = Lead(business_id=business_id, owner_id=user_id, stage=stage_enum)
            session.add(lead)
        else:
            old_stage = lead.stage.value if hasattr(lead.stage, "value") else str(lead.stage)
            lead.stage = stage_enum

        audit_activity = Activity(
            business_id=business.id,
            user_id=user_id,
            type=ActivityType.STATUS_CHANGED,
            channel="crm",
            outcome=f"Stage updated to {stage_enum.value}",
            notes=f"Pipeline stage moved from '{old_stage}' to '{stage_enum.value}'",
            entity_type="lead",
            entity_id=lead.id if lead else None,
        )
        session.add(audit_activity)
        await session.commit()

        return StageUpdateResponse(
            message="Stage updated successfully",
            business_id=business_id,
            old_stage=old_stage,
            new_stage=stage_enum.value,
        )

    @staticmethod
    async def bulk_update_stage(
        session: AsyncSession,
        business_ids: list[int],
        stage: str,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """Bulk updates pipeline stage for multiple businesses."""
        if not business_ids:
            return {"updated_count": 0, "business_ids": []}

        target_stage = PipelineStage.LEAD
        for s in PipelineStage:
            if s.value.lower() == stage.lower() or s.name.lower() == stage.lower():
                target_stage = s
                break

        stmt = (
            update(Lead)
            .where(Lead.business_id.in_(business_ids))
            .values(stage=target_stage, updated_at=datetime.now(UTC))
        )
        await session.execute(stmt)

        for b_id in business_ids:
            session.add(
                Activity(
                    business_id=b_id,
                    user_id=user_id,
                    type=ActivityType.STATUS_CHANGED,
                    channel="crm",
                    outcome=f"Stage updated to {target_stage.value}",
                    notes="Pipeline stage updated via bulk action",
                    entity_type="lead",
                    entity_id=b_id,
                )
            )
        await session.commit()
        return {
            "updated_count": len(business_ids),
            "business_ids": business_ids,
            "stage": target_stage.value,
        }
