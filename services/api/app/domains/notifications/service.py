"""FastUI Notifications Domain Service.

Device registry management, VAPID key distribution, targeted user push broadcasts,
and system-wide sales alert dispatching.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User
from app.domains.notifications.models import PushSubscription
from app.domains.notifications.schemas import PushSubscriptionCreate
from app.infrastructure.notifications.push_client import get_public_key, send_web_push
from app.shared.exceptions import ValidationError

logger = logging.getLogger("fastui.notifications")


class NotificationService:
    """Service managing push notification subscriptions and message broadcasts."""

    @staticmethod
    def get_vapid_public_key() -> str:
        """Returns the VAPID public key needed by browser PushManager to subscribe."""
        return get_public_key()

    @staticmethod
    async def subscribe(
        session: AsyncSession,
        payload: PushSubscriptionCreate,
        user: User,
    ) -> PushSubscription:
        """Registers or updates a browser Web Push subscription."""
        if not payload.endpoint or not payload.keys.p256dh or not payload.keys.auth:
            raise ValidationError("Subscription endpoint and cryptographic keys are required.")

        stmt = select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
        result = await session.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.user_id = user.id
            subscription.p256dh = payload.keys.p256dh
            subscription.auth = payload.keys.auth
            subscription.user_agent = payload.user_agent
        else:
            subscription = PushSubscription(
                user_id=user.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
                user_agent=payload.user_agent,
            )
            session.add(subscription)

        await session.commit()
        await session.refresh(subscription)
        return subscription

    @staticmethod
    async def unsubscribe(session: AsyncSession, endpoint: str, user_id: int | None = None) -> None:
        """Unregisters a push subscription endpoint, optionally scoped to user."""
        stmt = delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
        if user_id is not None:
            stmt = stmt.where(PushSubscription.user_id == user_id)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def send_notification(
        subscription_info: Any,
        payload: dict[str, Any],
        ttl: int = 86400,
    ) -> bool:
        """Helper to dispatch a push notification given a subscription dict or PushSubscription model."""
        if isinstance(subscription_info, dict):
            endpoint = subscription_info.get("endpoint")
            keys = subscription_info.get("keys", {})
            p256dh = subscription_info.get("p256dh") or (
                keys.get("p256dh") if isinstance(keys, dict) else None
            )
            auth = subscription_info.get("auth") or (
                keys.get("auth") if isinstance(keys, dict) else None
            )
        else:
            endpoint = getattr(subscription_info, "endpoint", None)
            p256dh = getattr(subscription_info, "p256dh", None)
            auth = getattr(subscription_info, "auth", None)

        return await send_web_push(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            payload=payload,
            ttl=ttl,
        )

    @classmethod
    async def broadcast_to_user(
        cls,
        session: AsyncSession,
        user_id: int,
        payload: dict[str, Any],
        ttl: int = 86400,
    ) -> dict[str, Any]:
        """Broadcasts push notification to all unique active devices of a user."""
        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
        res = await session.execute(stmt)
        all_subs = list(res.scalars().all())

        if not all_subs:
            return {
                "user_id": user_id,
                "total_subscriptions": 0,
                "unique_devices": 0,
                "dispatched_devices": 0,
                "failed_devices": 0,
                "cleaned_up_devices": 0,
            }

        # Deduplicate by endpoint
        unique_map: dict[str, PushSubscription] = {}
        redundant_subs: list[PushSubscription] = []

        for sub in all_subs:
            endpoint = (sub.endpoint or "").strip()
            if not endpoint or endpoint in unique_map or not sub.p256dh or not sub.auth:
                redundant_subs.append(sub)
            else:
                unique_map[endpoint] = sub

        valid_subs = list(unique_map.values())

        async def _dispatch(sub: PushSubscription) -> tuple[PushSubscription, bool]:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth,
                },
            }
            success = await cls.send_notification(
                sub_info,
                payload,
                ttl,
            )
            return sub, success

        tasks = [_dispatch(sub) for sub in valid_subs]
        results = await asyncio.gather(*tasks) if tasks else []

        dispatched = 0
        failed = 0
        stale_to_delete: list[PushSubscription] = list(redundant_subs)

        for sub, success in results:
            if success:
                dispatched += 1
            else:
                failed += 1
                stale_to_delete.append(sub)

        if stale_to_delete:
            for stale_sub in stale_to_delete:
                await session.delete(stale_sub)
            await session.commit()

        return {
            "user_id": user_id,
            "total_subscriptions": len(all_subs),
            "unique_devices": len(valid_subs),
            "dispatched_devices": dispatched,
            "failed_devices": failed,
            "cleaned_up_devices": len(stale_to_delete),
        }

    @classmethod
    async def broadcast_to_all_accounts(
        cls,
        session: AsyncSession,
        payload: dict[str, Any],
        ttl: int = 86400,
    ) -> dict[str, Any]:
        """Broadcasts push notification to all registered sales devices system-wide."""
        stmt = select(PushSubscription)
        res = await session.execute(stmt)
        all_subs = list(res.scalars().all())

        if not all_subs:
            return {
                "total_accounts": 0,
                "total_subscriptions": 0,
                "unique_devices": 0,
                "dispatched_devices": 0,
                "failed_devices": 0,
                "cleaned_up_devices": 0,
            }

        unique_map: dict[str, PushSubscription] = {}
        redundant_subs: list[PushSubscription] = []
        user_ids = set()

        for sub in all_subs:
            if sub.user_id:
                user_ids.add(sub.user_id)
            endpoint = (sub.endpoint or "").strip()
            if not endpoint or endpoint in unique_map or not sub.p256dh or not sub.auth:
                redundant_subs.append(sub)
            else:
                unique_map[endpoint] = sub

        valid_subs = list(unique_map.values())

        async def _dispatch(sub: PushSubscription) -> tuple[PushSubscription, bool]:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth,
                },
            }
            success = await cls.send_notification(
                sub_info,
                payload,
                ttl,
            )
            return sub, success

        tasks = [_dispatch(sub) for sub in valid_subs]
        results = await asyncio.gather(*tasks) if tasks else []

        dispatched = 0
        failed = 0
        stale_to_delete: list[PushSubscription] = list(redundant_subs)

        for sub, success in results:
            if success:
                dispatched += 1
            else:
                failed += 1
                stale_to_delete.append(sub)

        if stale_to_delete:
            for stale_sub in stale_to_delete:
                await session.delete(stale_sub)
            await session.commit()

        return {
            "total_accounts": len(user_ids),
            "total_subscriptions": len(all_subs),
            "unique_devices": len(valid_subs),
            "dispatched_devices": dispatched,
            "failed_devices": failed,
            "cleaned_up_devices": len(stale_to_delete),
        }
