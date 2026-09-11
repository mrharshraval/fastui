"""FastUI Pipeline Domain Service.

Provides Kanban board transformations, deal probabilities, and pipeline analytics over Lead entities.
"""

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.models import Business
from app.domains.leads.models import Lead


class PipelineService:
    """Service formatting leads into deal cards for the Kanban pipeline board."""

    @staticmethod
    async def get_pipeline_deals(session: AsyncSession) -> list[dict[str, Any]]:
        """Returns all active pipeline leads formatted for the Pipeline board view."""
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
            "lost": "Qualification",
        }

        probability_map = {
            "lead": 20,
            "contacted": 40,
            "qualified": 60,
            "proposal": 80,
            "won": 100,
            "lost": 0,
        }

        deals = []
        for business, lead in rows:
            raw_stage = (
                lead.stage.value if hasattr(lead.stage, "value") else str(lead.stage).lower()
            )
            board_stage = stage_map.get(raw_stage, "Qualification")
            deals.append(
                {
                    "id": str(business.id),
                    "business_name": business.business_name,
                    "stage": board_stage,
                    "value": (lead.score or 50) * 100,
                    "probability": probability_map.get(raw_stage, 50),
                    "priority": (
                        lead.priority.value
                        if hasattr(lead.priority, "value")
                        else str(lead.priority)
                    ),
                    "lead_id": lead.id,
                    "city": business.city,
                    "category": business.category,
                }
            )
        return deals
