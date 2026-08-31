import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post("/subscribe", response_model=PushSubscriptionResponse)
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


@router.delete("/unsubscribe")
async def unsubscribe_push_notifications(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Removes a push subscription for the active user.
    """
    stmt = delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
    await db.execute(stmt)
    await db.commit()
    return {"status": "unsubscribed"}


@router.post("/test")
async def send_test_notification(
    payload: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Sends an immediate test push notification to all devices registered by the user.
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

    stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
    res = await db.execute(stmt)
    subscriptions = list(res.scalars().all())

    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No push subscriptions registered for this device or account."
        )

    notification_payload = {
        "title": payload.title or "FastUI Reminder",
        "body": payload.body or "This is a test notification from FastUI.",
        "icon": "/assets/brand/favicon/brand/primary/filled.png",
        "badge": "/assets/brand/favicon/brand/primary/filled.png",
        "data": {
            "url": payload.url or "/prospects",
        }
    }

    dispatched = 0
    for sub in subscriptions:
        sub_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth,
            }
        }
        success = PushNotificationService.send_notification(sub_info, notification_payload)
        if success:
            dispatched += 1
        else:
            await db.delete(sub)

    await db.commit()
    return {
        "status": "sent",
        "dispatched_devices": dispatched,
        "total_registered": len(subscriptions),
    }
