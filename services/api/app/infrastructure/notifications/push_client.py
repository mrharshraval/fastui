"""FastUI Low-Level WebPush Client.

Encapsulates VAPID keypair management, payload encryption, and synchronous network I/O
wrapped in asyncio.to_thread to guarantee zero event-loop blocking.
"""

import asyncio
import base64
import json
import logging
from typing import Any

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Ephemeral in-memory fallback for local development or testing when environment variables are omitted
_in_memory_vapid_keys: tuple[str, str] | None = None


def get_or_create_vapid_keys() -> tuple[str, str]:
    """Returns (public_key_base64, private_key_pem_or_base64).

    Strictly uses VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY from settings.
    Falls back to ephemeral in-memory generated keys for local dev / testing.
    """
    global _in_memory_vapid_keys

    if settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY:
        return settings.VAPID_PUBLIC_KEY, settings.VAPID_PRIVATE_KEY

    if _in_memory_vapid_keys:
        return _in_memory_vapid_keys

    logger.warning("VAPID keys not configured; generating ephemeral in-memory keypair.")
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


def get_public_key() -> str:
    """Returns the base64-encoded VAPID public key."""
    pub_key, _ = get_or_create_vapid_keys()
    return pub_key


def _sync_send_notification(
    subscription_info: dict[str, Any],
    payload: dict[str, Any],
    ttl: int = 86400,
) -> bool:
    """Synchronous network I/O call to pywebpush."""
    _, priv_key = get_or_create_vapid_keys()
    claim_email = settings.VAPID_CLAIM_EMAIL or "notifications@fastui.in"

    vapid_claims = {"sub": f"mailto:{claim_email}"}

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=priv_key,
            vapid_claims=vapid_claims,
            ttl=ttl,
        )
        logger.info(
            f"Dispatched push notification to {subscription_info.get('endpoint', '')[:40]}..."
        )
        return True
    except WebPushException as ex:
        status_code = getattr(ex.response, "status_code", None) if ex.response else None
        if status_code in (404, 410):
            logger.warning(
                f"Push subscription expired or unsubscribed (HTTP {status_code}): "
                f"{subscription_info.get('endpoint', '')[:40]}"
            )
            return False
        logger.error(f"Failed to deliver Web Push notification: {ex}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error delivering Web Push notification: {e}")
        return False


async def send_web_push(
    endpoint: str,
    p256dh: str,
    auth: str,
    payload: dict[str, Any],
    ttl: int = 86400,
) -> bool:
    """Dispatches an encrypted Web Push notification asynchronously without blocking the event loop."""
    subscription_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": p256dh,
            "auth": auth,
        },
    }
    return await asyncio.to_thread(_sync_send_notification, subscription_info, payload, ttl)
