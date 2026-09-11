"""FastUI Notifications Domain API Routes.

Exposes WebPush subscription management and targeted push notification dispatch.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.models import UserRole
from app.domains.auth.schemas import TokenData
from app.domains.notifications.schemas import (
    BroadcastNotificationRequest,
    BroadcastNotificationResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    TestNotificationRequest,
    VapidPublicKeyResponse,
)
from app.domains.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/vapid-public-key",
    response_model=VapidPublicKeyResponse,
    summary="Get VAPID Public Key",
)
async def get_vapid_public_key() -> VapidPublicKeyResponse:
    """Returns the base64-encoded VAPID public key needed by browser PushManager."""
    key = NotificationService.get_vapid_public_key()
    return VapidPublicKeyResponse(public_key=key)


@router.post(
    "/subscribe",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to Push Notifications",
)
async def subscribe_push_notifications(
    payload: PushSubscriptionCreate,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> PushSubscriptionResponse:
    """Registers or updates a browser Web Push subscription."""
    sub = await NotificationService.subscribe(
        session=session,
        payload=payload,
        user=current_user,
    )
    return PushSubscriptionResponse(
        id=sub.id,
        endpoint=sub.endpoint,
        created_at=sub.created_at,
    )


@router.delete(
    "/unsubscribe",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unsubscribe from Push Notifications",
)
async def unsubscribe_push_notifications(
    endpoint: str,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    """Removes a push subscription endpoint."""
    await NotificationService.unsubscribe(
        session=session,
        endpoint=endpoint,
        user_id=current_user.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/test",
    summary="Send Test Push Notification",
)
async def send_test_notification(
    payload: TestNotificationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> dict[str, Any]:
    """Sends a test push notification to all devices registered by current user."""
    notification_payload = {
        "title": payload.title or "FastUI Reminder",
        "body": payload.body or "This is a test notification from FastUI.",
        "icon": "/assets/brand/icon/monochrome/white/solid.png",
        "badge": "/assets/brand/notification/badge/monochrome/white/solid.png",
        "data": {
            "url": payload.url or "/prospects",
        },
    }
    metrics = await NotificationService.broadcast_to_user(
        session=session,
        user_id=current_user.id,
        payload=notification_payload,
    )
    if metrics["total_subscriptions"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No push subscriptions registered for this device or account.",
        )
    return {
        "status": "sent" if metrics["dispatched_devices"] > 0 else "failed",
        "dispatched_devices": metrics["dispatched_devices"],
        "total_registered": metrics["unique_devices"],
        "cleaned_up_devices": metrics["cleaned_up_devices"],
    }


@router.post(
    "/broadcast",
    response_model=BroadcastNotificationResponse,
    summary="Broadcast Push Notification",
)
async def broadcast_notification(
    payload: BroadcastNotificationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> BroadcastNotificationResponse:
    """Broadcasts a push notification to specific users or all registered accounts."""
    notification_data: dict[str, Any] = {
        "url": payload.url or "/prospects",
    }
    if payload.business_id is not None:
        notification_data["business_id"] = payload.business_id

    notification_payload: dict[str, Any] = {
        "title": payload.title,
        "body": payload.body,
        "icon": "/assets/brand/icon/monochrome/white/solid.png",
        "badge": "/assets/brand/notification/badge/monochrome/white/solid.png",
        "data": notification_data,
    }
    if payload.tag:
        notification_payload["tag"] = payload.tag

    if payload.all_accounts:
        metrics = await NotificationService.broadcast_to_all_accounts(
            session=session,
            payload=notification_payload,
        )
        status_str = (
            "sent"
            if metrics["dispatched_devices"] > 0
            else ("no_subscriptions" if metrics["total_subscriptions"] == 0 else "failed")
        )
        return BroadcastNotificationResponse(
            status=status_str,
            user_id=None,
            total_accounts=metrics.get("total_accounts", 0),
            total_subscriptions=metrics["total_subscriptions"],
            unique_devices=metrics["unique_devices"],
            dispatched_devices=metrics["dispatched_devices"],
            failed_devices=metrics["failed_devices"],
            cleaned_up_devices=metrics["cleaned_up_devices"],
        )

    target_user_id = payload.user_id or current_user.id
    user_role_str = str(current_user.role).lower()
    if (
        payload.user_id
        and payload.user_id != current_user.id
        and user_role_str != UserRole.ADMIN.value.lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can broadcast notifications to other users.",
        )

    metrics = await NotificationService.broadcast_to_user(
        session=session,
        user_id=target_user_id,
        payload=notification_payload,
    )
    status_str = (
        "sent"
        if metrics["dispatched_devices"] > 0
        else ("no_subscriptions" if metrics["total_subscriptions"] == 0 else "failed")
    )
    return BroadcastNotificationResponse(
        status=status_str,
        user_id=target_user_id,
        total_accounts=1,
        total_subscriptions=metrics["total_subscriptions"],
        unique_devices=metrics["unique_devices"],
        dispatched_devices=metrics["dispatched_devices"],
        failed_devices=metrics["failed_devices"],
        cleaned_up_devices=metrics["cleaned_up_devices"],
    )
