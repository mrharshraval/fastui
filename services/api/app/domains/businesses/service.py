"""FastUI Business Domain Service.

Authoritative business query, retrieval, mutation, and atomic cascade lifecycle management.
Decoupled from HTTP transport.
"""

import logging
from typing import Any

from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.models import Business, BusinessSource
from app.domains.businesses.normalizer import BusinessNameNormalizer
from app.domains.businesses.schemas import (
    BulkDeleteResponse,
    BusinessResponse,
    BusinessUpdateRequest,
)
from app.domains.leads.models import Lead, LeadPriority, LeadSignal, PipelineStage
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


from app.domains.businesses.mapping import map_business_response


class BusinessService:
    """Service managing master Business entity query, update, and deletion lifecycle."""

    @staticmethod
    async def list_businesses(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_lead: bool | None = None,
        stage: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[BusinessResponse]:
        """Fetches business records across the system with optional lead status and stage filters."""
        query = select(Business, Lead).outerjoin(Lead, Business.id == Lead.business_id)

        if is_lead is True:
            query = query.where(Lead.id.isnot(None))
        elif is_lead is False:
            query = query.where(Lead.id.is_(None))

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
    async def get_business_by_id(session: AsyncSession, business_id: int) -> BusinessResponse:
        """Fetches a single business by ID with associated Lead and maps metadata."""
        query = (
            select(Business, Lead)
            .outerjoin(Lead, Business.id == Lead.business_id)
            .where(Business.id == business_id)
        )
        result = await session.execute(query)
        row = result.first()
        if not row:
            raise EntityNotFoundError("Business", business_id)

        business, lead = row

        maps_source_stmt = select(BusinessSource).where(
            BusinessSource.business_id == business_id,
            BusinessSource.platform == "google_maps",
        )
        maps_source_res = await session.execute(maps_source_stmt)
        maps_source = maps_source_res.scalars().first()

        return map_business_response(business, lead, maps_source)

    @staticmethod
    async def update_business(
        session: AsyncSession,
        business_id: int,
        req: BusinessUpdateRequest,
        user_id: int | None = None,
    ) -> BusinessResponse:
        """Updates business fields and associated lead state."""
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        if req.business_name is not None:
            clean_name = req.business_name.strip()
            business.business_name = clean_name
            norm = BusinessNameNormalizer.normalize(clean_name)
            business.canonical_name = norm.display_name
            business.normalized_business_name = norm.normalized_name

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

        # Update lead properties if lead exists
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

        await session.commit()
        await session.refresh(business)
        return await BusinessService.get_business_by_id(session=session, business_id=business_id)

    @staticmethod
    async def delete_business(session: AsyncSession, business_id: int) -> dict[str, Any]:
        """Atomically deletes a business and all cascade children."""
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        name = business.business_name
        deleted = await BusinessService.cascade_delete_businesses(session, [business_id])
        if not deleted:
            raise EntityNotFoundError("Business", business_id)

        return {"status": "deleted", "id": business_id, "name": name}

    @staticmethod
    async def bulk_delete_businesses(
        session: AsyncSession,
        business_ids: list[int],
    ) -> BulkDeleteResponse:
        """Atomically deletes multiple businesses and all cascade children."""
        if not business_ids:
            return BulkDeleteResponse(
                message="No business IDs provided", deleted_count=0, business_ids=[]
            )

        deleted_ids = await BusinessService.cascade_delete_businesses(session, business_ids)
        return BulkDeleteResponse(
            message=f"Successfully deleted {len(deleted_ids)} records",
            deleted_count=len(deleted_ids),
            business_ids=deleted_ids,
        )

    @staticmethod
    async def cascade_delete_businesses(
        session: AsyncSession,
        business_ids: list[int],
    ) -> list[int]:
        """Topological, set-based deletion of businesses and child entities."""
        from sqlalchemy import delete, update

        from app.domains.demos.models import DemoEvent, ProspectDemo
        from app.domains.engagement.models import (
            Activity,
            Contact,
            Interaction,
            Note,
            Outreach,
            Reminder,
            Task,
        )
        from app.domains.enrichment.models import CrawledWebsite

        if not business_ids:
            return []

        existing_stmt = select(Business.id).where(Business.id.in_(business_ids))
        existing_res = await session.execute(existing_stmt)
        valid_ids = list(existing_res.scalars().all())
        if not valid_ids:
            return []

        # 1. Demos and demo events
        demo_stmt = select(ProspectDemo.id).where(ProspectDemo.business_id.in_(valid_ids))
        demo_ids = list((await session.execute(demo_stmt)).scalars().all())
        if demo_ids:
            await session.execute(delete(DemoEvent).where(DemoEvent.demo_id.in_(demo_ids)))
            await session.execute(delete(ProspectDemo).where(ProspectDemo.id.in_(demo_ids)))

        # 2. Activities and touchpoints
        await session.execute(delete(Activity).where(Activity.business_id.in_(valid_ids)))
        await session.execute(delete(Interaction).where(Interaction.business_id.in_(valid_ids)))
        await session.execute(delete(Outreach).where(Outreach.business_id.in_(valid_ids)))

        # 3. Tasks, reminders, notes
        await session.execute(delete(Reminder).where(Reminder.business_id.in_(valid_ids)))
        await session.execute(delete(Task).where(Task.business_id.in_(valid_ids)))
        await session.execute(delete(Note).where(Note.business_id.in_(valid_ids)))

        # 4. Sources and crawled websites
        await session.execute(
            delete(BusinessSource).where(BusinessSource.business_id.in_(valid_ids))
        )
        await session.execute(
            update(CrawledWebsite)
            .where(CrawledWebsite.business_id.in_(valid_ids))
            .values(business_id=None)
        )

        # 5. Contacts and leads
        await session.execute(delete(Contact).where(Contact.business_id.in_(valid_ids)))
        await session.execute(delete(Lead).where(Lead.business_id.in_(valid_ids)))

        # 6. Master businesses
        await session.execute(delete(Business).where(Business.id.in_(valid_ids)))
        await session.commit()
        return valid_ids
