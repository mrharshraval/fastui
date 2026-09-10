import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db

from models.schema import PushSubscription, User
from schemas.auth import TokenData
from schemas.notifications import (
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    VapidPublicKeyResponse,
    TestNotificationRequest,
    BroadcastNotificationRequest,
    BroadcastNotificationResponse,
)
from services.auth_service import get_current_user
from services.push_service import PushNotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key():
    """
    Returns the VAPID public key needed by browser PushManager to subscribe.
    """
    public_key = PushNotificationService.get_public_key()
    return VapidPublicKeyResponse(public_key=public_key)


@router.post("/subscriptions", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_push_notifications(
    payload: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Registers or updates a browser/phone Web Push subscription.
    """
    # 1. Resolve user ID
    user_id = current_user.user_id
    if not user_id and current_user.email:
        user_stmt = select(User).where(User.email == current_user.email)
        user_res = await db.execute(user_stmt)
        user_obj = user_res.scalar_one_or_none()
        if user_obj:
            user_id = user_obj.id

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to identify user account for push subscription."
        )

    # 2. Check if this endpoint is already registered
    stmt = select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    res = await db.execute(stmt)
    subscription = res.scalar_one_or_none()

    if subscription:
        # Update keys and user association
        subscription.user_id = user_id
        subscription.p256dh = payload.keys.p256dh
        subscription.auth = payload.keys.auth
        subscription.user_agent = payload.user_agent
        subscription.updated_at = datetime.now(timezone.utc)
    else:
        # Create new subscription
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh,
            auth=payload.keys.auth,
            user_agent=payload.user_agent,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(subscription)

    await db.commit()
    await db.refresh(subscription)
    logger.info(f"Registered push subscription {subscription.id} for user {user_id}")
    return subscription


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_push_notifications(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Removes a push subscription for the active user.
    Scoped to current user — cannot remove another user's subscription.
    """
    stmt = delete(PushSubscription).where(
        PushSubscription.endpoint == endpoint,
        PushSubscription.user_id == current_user.user_id
    )
    await db.execute(stmt)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/dispatches")
async def send_test_notification(
    payload: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Sends an immediate test push notification to all devices registered by the user.
    Deduplicates devices and cleans up invalid subscriptions automatically.
    """
    user_id = current_user.user_id
    if not user_id and current_user.email:
        user_stmt = select(User).where(User.email == current_user.email)
        user_res = await db.execute(user_stmt)
        user_obj = user_res.scalar_one_or_none()
        if user_obj:
            user_id = user_obj.id

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to identify user account."
        )

    notification_payload = {
        "title": payload.title or "FastUI Reminder",
        "body": payload.body or "This is a test notification from FastUI.",
        "icon": "/assets/brand/icon/monochrome/white/solid.png",
        "badge": "/assets/brand/notification/badge/monochrome/white/solid.png",
        "data": {
            "url": payload.url or "/prospects",
        }
    }

    metrics = await PushNotificationService.broadcast_to_user(
        session=db,
        user_id=user_id,
        payload=notification_payload,
    )

    if metrics["total_subscriptions"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No push subscriptions registered for this device or account."
        )

    return {
        "status": "sent" if metrics["dispatched_devices"] > 0 else "failed",
        "dispatched_devices": metrics["dispatched_devices"],
        "total_registered": metrics["unique_devices"],
        "cleaned_up_devices": metrics["cleaned_up_devices"],
    }


@router.post("/broadcasts", response_model=BroadcastNotificationResponse)
async def broadcast_notification(
    payload: BroadcastNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Broadcasts a push notification to all active, valid device subscriptions
    for the intended user, delivering it to every subscribed device without duplicates.
    """
    # 1. Resolve target user ID
    target_user_id = payload.user_id or current_user.user_id
    if not target_user_id and current_user.email:
        user_stmt = select(User).where(User.email == current_user.email)
        user_res = await db.execute(user_stmt)
        user_obj = user_res.scalar_one_or_none()
        if user_obj:
            target_user_id = user_obj.id

    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to identify target user account for broadcast."
        )

    # 2. Construct rich notification payload
    notification_data: Dict[str, Any] = {
        "url": payload.url or "/prospects",
    }
    if payload.business_id is not None:
        notification_data["business_id"] = payload.business_id

    notification_payload: Dict[str, Any] = {
        "title": payload.title,
        "body": payload.body,
        "icon": "/assets/brand/icon/monochrome/white/solid.png",
        "badge": "/assets/brand/notification/badge/monochrome/white/solid.png",
        "data": notification_data,
    }
    if payload.tag:
        notification_payload["tag"] = payload.tag

    # 3. All accounts broadcast mode
    caller_role = getattr(current_user.role, "value", str(current_user.role or ""))
    if payload.all_accounts:
        metrics = await PushNotificationService.broadcast_to_all_accounts(
            session=db,
            payload=notification_payload,
        )
        status_str = "sent" if metrics["dispatched_devices"] > 0 else (
            "no_subscriptions" if metrics["total_subscriptions"] == 0 else "failed"
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

    # 4. Specific user targeting mode
    if payload.user_id and payload.user_id != current_user.user_id and caller_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can broadcast notifications to other users."
        )

    metrics = await PushNotificationService.broadcast_to_user(
        session=db,
        user_id=target_user_id,
        payload=notification_payload,
    )

    status_str = "sent" if metrics["dispatched_devices"] > 0 else (
        "no_subscriptions" if metrics["total_subscriptions"] == 0 else "failed"
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


