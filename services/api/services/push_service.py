import asyncio
import base64
import json
import logging
from typing import Any, Dict, Optional, List

from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException
from py_vapid import Vapid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.schema import PushSubscription

logger = logging.getLogger(__name__)

# Ephemeral in-memory fallback for local development or testing when environment variables are omitted
_in_memory_vapid_keys: Optional[tuple[str, str]] = None


def get_or_create_vapid_keys() -> tuple[str, str]:
    """
    Returns (public_key_base64, private_key_pem_or_base64).
    Strictly uses VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY from environment variables / settings.
    Falls back to ephemeral in-memory generated keys for local dev / testing.
    """
    global _in_memory_vapid_keys

    if settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY:
        return settings.VAPID_PUBLIC_KEY, settings.VAPID_PRIVATE_KEY

    # In-memory cached keypair (e.g. for dev/testing when env vars aren't provided)
    if _in_memory_vapid_keys:
        return _in_memory_vapid_keys

    logger.warning("VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY not found in environment; generating ephemeral in-memory keypair.")
    vapid = Vapid()
    vapid.generate_keys()

    raw_bytes = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64_str = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")
    priv_pem = vapid.private_pem().decode("utf-8")

    _in_memory_vapid_keys = (pub_b64_str, priv_pem)
    return _in_memory_vapid_keys


class PushNotificationService:
    """
    Standard Web Push Service managing payload encryption and dispatching via VAPID.
    """

    @classmethod
    def get_public_key(cls) -> str:
        pub_key, _ = get_or_create_vapid_keys()
        return pub_key

    @classmethod
    def send_notification(
        cls,
        subscription_info: Dict[str, Any],
        payload: Dict[str, Any],
        ttl: int = 86400,
    ) -> bool:
        """
        Sends an encrypted Web Push notification to a browser/phone endpoint.
        Returns True on success, False if subscription is expired/invalid (404/410).
        """
        _, priv_key = get_or_create_vapid_keys()
        claim_email = settings.VAPID_CLAIM_EMAIL or "notifications@fastui.in"

        vapid_claims = {
            "sub": f"mailto:{claim_email}"
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=priv_key,
                vapid_claims=vapid_claims,
                ttl=ttl,
            )
            logger.info(f"Successfully dispatched push notification to {subscription_info.get('endpoint', '')[:40]}...")
            return True
        except WebPushException as ex:
            # Check response status for expired subscriptions
            status_code = getattr(ex.response, "status_code", None) if ex.response else None
            if status_code in (404, 410):
                logger.warning(f"Push subscription has expired or unsubscribed (HTTP {status_code}). Endpoint: {subscription_info.get('endpoint', '')[:40]}")
                return False
            logger.error(f"Failed to deliver Web Push notification: {ex}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error delivering Web Push notification: {e}")
            return False

    @classmethod
    async def broadcast_to_user(
        cls,
        session: AsyncSession,
        user_id: int,
        payload: Dict[str, Any],
        ttl: int = 86400,
    ) -> Dict[str, Any]:
        """
        Broadcasts a push notification to ALL active, valid device subscriptions
        for the specified user, guaranteeing:
        1. Strict deduplication by endpoint (delivers to every unique device without duplicates).
        2. Concurrent non-blocking dispatch across all unique devices via asyncio.to_thread.
        3. Automatic purging of expired/stale subscriptions (HTTP 404/410, revoked or corrupted keys).
        4. Structured delivery metrics returned to caller.
        """
        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
        res = await session.execute(stmt)
        all_subs = list(res.scalars().all())

        if not all_subs:
            logger.info(f"No push subscriptions found for user {user_id}.")
            return {
                "user_id": user_id,
                "total_subscriptions": 0,
                "unique_devices": 0,
                "dispatched_devices": 0,
                "failed_devices": 0,
                "cleaned_up_devices": 0,
            }

        # 1. Deduplicate subscriptions strictly by endpoint
        # If multiple records share the same endpoint, keep one and queue redundant ones for cleanup
        unique_map: Dict[str, PushSubscription] = {}
        redundant_subs: List[PushSubscription] = []

        for sub in all_subs:
            endpoint = (sub.endpoint or "").strip()
            if not endpoint:
                redundant_subs.append(sub)
                continue
            if endpoint in unique_map:
                redundant_subs.append(sub)
            else:
                unique_map[endpoint] = sub

        unique_subs = list(unique_map.values())

        # 2. Filter valid crypto keys (must have non-empty p256dh and auth)
        valid_subs: List[PushSubscription] = []
        for sub in unique_subs:
            if not sub.p256dh or not sub.auth:
                redundant_subs.append(sub)
            else:
                valid_subs.append(sub)

        # 3. Concurrently dispatch notifications to all unique valid devices
        async def _dispatch_single(sub: PushSubscription) -> tuple[PushSubscription, bool]:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth,
                },
            }
            try:
                # pywebpush is synchronous network I/O; run in thread to keep event loop unblocked
                success = await asyncio.to_thread(cls.send_notification, sub_info, payload, ttl)
                return sub, success
            except Exception as ex:
                logger.error(f"Error during async push dispatch to {sub.endpoint[:40]}: {ex}")
                return sub, False

        tasks = [_dispatch_single(sub) for sub in valid_subs]
        results = await asyncio.gather(*tasks) if tasks else []

        dispatched = 0
        failed = 0
        stale_to_delete: List[PushSubscription] = list(redundant_subs)

        for sub, success in results:
            if success:
                dispatched += 1
            else:
                failed += 1
                stale_to_delete.append(sub)

        # 4. Clean up stale/invalid/redundant subscriptions
        if stale_to_delete:
            for stale_sub in stale_to_delete:
                await session.delete(stale_sub)
            await session.commit()
            logger.info(f"Cleaned up {len(stale_to_delete)} stale/redundant push subscriptions for user {user_id}.")

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
        payload: Dict[str, Any],
        ttl: int = 86400,
    ) -> Dict[str, Any]:
        """
        Broadcasts a push notification to ALL registered accounts and their active devices,
        guaranteeing:
        1. Strict deduplication by endpoint (every subscribed device gets exactly one notification).
        2. Concurrent non-blocking dispatch across all devices.
        3. Automatic purging of expired/stale subscriptions.
        4. Consolidated metrics.
        """
        stmt = select(PushSubscription)
        res = await session.execute(stmt)
        all_subs = list(res.scalars().all())

        if not all_subs:
            logger.info("No push subscriptions found in system.")
            return {
                "total_accounts": 0,
                "total_subscriptions": 0,
                "unique_devices": 0,
                "dispatched_devices": 0,
                "failed_devices": 0,
                "cleaned_up_devices": 0,
            }

        # 1. Deduplicate by endpoint
        unique_map: Dict[str, PushSubscription] = {}
        redundant_subs: List[PushSubscription] = []
        user_ids = set()

        for sub in all_subs:
            if sub.user_id:
                user_ids.add(sub.user_id)
            endpoint = (sub.endpoint or "").strip()
            if not endpoint:
                redundant_subs.append(sub)
                continue
            if endpoint in unique_map:
                redundant_subs.append(sub)
            else:
                unique_map[endpoint] = sub

        unique_subs = list(unique_map.values())

        # 2. Filter valid crypto keys
        valid_subs: List[PushSubscription] = []
        for sub in unique_subs:
            if not sub.p256dh or not sub.auth:
                redundant_subs.append(sub)
            else:
                valid_subs.append(sub)

        # 3. Concurrent dispatch
        async def _dispatch_single(sub: PushSubscription) -> tuple[PushSubscription, bool]:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth,
                },
            }
            try:
                success = await asyncio.to_thread(cls.send_notification, sub_info, payload, ttl)
                return sub, success
            except Exception as ex:
                logger.error(f"Error during broadcast push dispatch to {sub.endpoint[:40]}: {ex}")
                return sub, False

        tasks = [_dispatch_single(sub) for sub in valid_subs]
        results = await asyncio.gather(*tasks) if tasks else []

        dispatched = 0
        failed = 0
        stale_to_delete: List[PushSubscription] = list(redundant_subs)

        for sub, success in results:
            if success:
                dispatched += 1
            else:
                failed += 1
                stale_to_delete.append(sub)

        # 4. Clean up stale subscriptions
        if stale_to_delete:
            for stale_sub in stale_to_delete:
                await session.delete(stale_sub)
            await session.commit()
            logger.info(f"Cleaned up {len(stale_to_delete)} stale/redundant push subscriptions during all-account broadcast.")

        return {
            "total_accounts": len(user_ids),
            "total_subscriptions": len(all_subs),
            "unique_devices": len(valid_subs),
            "dispatched_devices": dispatched,
            "failed_devices": failed,
            "cleaned_up_devices": len(stale_to_delete),
        }


