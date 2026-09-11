"""FastUI Demos Domain API Routes.

Unified canonical endpoints under /v1 for:
1. Public interactive prospect demos (governed by token validation policy).
2. Public demo telemetry tracking (governed by token validation policy).
3. Authenticated sales representative demo generation and metric retrieval.
"""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.schemas import TokenData
from app.domains.demos.schemas import (
    DemoCreateRequest,
    DemoEventCreate,
    DemoResponse,
    DentalDemoPresentation,
)
from app.domains.demos.service import DemoService, _dispatch_demo_event_push

router = APIRouter(tags=["Demos"])


# ─────────────────────────────────────────────────────────────
# TOKEN-VALIDATED PROSPECT DEMO ENDPOINTS
# ─────────────────────────────────────────────────────────────


@router.get(
    "/demos/{token}",
    response_model=DentalDemoPresentation,
    summary="Get Demo Presentation",
)
async def get_demo_by_token(
    token: str,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> DentalDemoPresentation:
    """Public presentation endpoint for prospect dental demos.

    Access is governed by unguessable 24-character token validation.
    Returns business presentation data with private cache control.
    """
    presentation = await DemoService.get_public_presentation(session=session, token=token)
    response.headers["Cache-Control"] = "private, max-age=300"
    return presentation


@router.post(
    "/demos/{token}/events",
    status_code=status.HTTP_201_CREATED,
    summary="Track Demo Telemetry Event",
)
async def track_demo_event(
    token: str,
    event_data: DemoEventCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Records visitor interaction events on a demo and triggers sales push alerts.

    Access is governed by unguessable 24-character token validation.
    """
    user_agent = request.headers.get("user-agent", "")
    result, notification_info = await DemoService.track_event(
        session=session,
        token=token,
        event_data=event_data,
        user_agent=user_agent,
    )

    if notification_info:
        biz_id, biz_name, evt_type = notification_info
        background_tasks.add_task(
            _dispatch_demo_event_push,
            business_id=biz_id,
            business_name=biz_name,
            event_type=evt_type,
        )

    return result


# ─────────────────────────────────────────────────────────────
# AUTHENTICATED BUSINESS DEMO MANAGEMENT
# ─────────────────────────────────────────────────────────────


@router.post(
    "/businesses/{business_id}/demo",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or Retrieve Demo",
)
async def create_or_get_prospect_demo(
    business_id: int,
    body: DemoCreateRequest | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> DemoResponse:
    """Generates an unguessable 24-character personalized website demo link for a business."""
    return await DemoService.create_or_get_demo(
        session=session,
        business_id=business_id,
        req=body,
        user_id=current_user.user_id,
    )


@router.get(
    "/businesses/{business_id}/demo",
    response_model=DemoResponse,
    summary="Get Business Demo",
)
async def get_business_demo(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> DemoResponse:
    """Fetches the active demo link and view metrics for a business."""
    return await DemoService.get_business_demo(
        session=session,
        business_id=business_id,
    )
