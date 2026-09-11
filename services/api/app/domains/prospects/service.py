"""FastUI Prospects Domain Service.

Specialized domain query and action view over uncontacted Business records (Lead is None).
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import asc, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.models import Business, BusinessSource
from app.domains.businesses.schemas import BusinessResponse
from app.domains.businesses.service import map_business_response
from app.domains.engagement.models import Activity, ActivityType
from app.domains.leads.models import Lead
from app.domains.prospects.schemas import BulkQualifyResponse
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class ProspectsService:
    """Service providing query and qualification views over unpromoted prospects."""

    @staticmethod
    async def list_prospects(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        qualification_status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[BusinessResponse]:
        """Fetches businesses that have NOT been converted to active sales leads (Lead is NULL)."""
        query = (
            select(Business, Lead)
            .outerjoin(Lead, Business.id == Lead.business_id)
            .where(Lead.id.is_(None))
        )

        if qualification_status and qualification_status.lower() != "all":
            query = query.where(Business.qualification_status == qualification_status.lower())

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
            "qualification_status": Business.qualification_status,
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
    async def qualify_prospect(
        session: AsyncSession,
        business_id: int,
        qualification_status: str,
        user_id: int | None = None,
    ) -> BusinessResponse:
        """Updates prospect qualification status and logs audit activity."""
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        old_status = business.qualification_status
        clean_status = qualification_status.lower()
        business.qualification_status = clean_status

        activity = Activity(
            business_id=business.id,
            user_id=user_id,
            type=ActivityType.STATUS_CHANGED,
            channel="crm",
            outcome=f"Qualification updated to {clean_status}",
            notes=f"Prospect qualification changed from '{old_status}' to '{clean_status}'",
            entity_type="business",
            entity_id=business.id,
        )
        session.add(activity)
        await session.commit()

        from app.domains.businesses.service import BusinessService

        return await BusinessService.get_business_by_id(session=session, business_id=business_id)

    @staticmethod
    async def bulk_qualify_prospects(
        session: AsyncSession,
        business_ids: list[int],
        qualification_status: str,
        user_id: int | None = None,
    ) -> BulkQualifyResponse:
        """Bulk updates qualification status for multiple businesses."""
        if not business_ids:
            return BulkQualifyResponse(
                updated_count=0, business_ids=[], status=qualification_status
            )

        clean_status = qualification_status.lower()
        stmt = (
            update(Business)
            .where(Business.id.in_(business_ids))
            .values(qualification_status=clean_status, updated_at=datetime.now(UTC))
        )
        await session.execute(stmt)

        for b_id in business_ids:
            session.add(
                Activity(
                    business_id=b_id,
                    user_id=user_id,
                    type=ActivityType.STATUS_CHANGED,
                    channel="crm",
                    outcome=f"Bulk qualified to {clean_status}",
                    notes=f"Qualification updated to '{clean_status}' via bulk action",
                    entity_type="business",
                    entity_id=b_id,
                )
            )
        await session.commit()
        return BulkQualifyResponse(
            updated_count=len(business_ids),
            business_ids=business_ids,
            status=clean_status,
        )
