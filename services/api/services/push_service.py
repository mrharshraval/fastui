import base64
import json
import logging
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException
from py_vapid import Vapid

from core.config import settings

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
