import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from pywebpush import webpush, WebPushException
from py_vapid import Vapid

from core.config import settings

logger = logging.getLogger(__name__)

VAPID_CACHE_FILE = Path(__file__).resolve().parent.parent / ".vapid_keys.json"


def get_or_create_vapid_keys() -> tuple[str, str]:
    """
    Returns (public_key_base64, private_key_pem_or_base64).
    If keys are set in settings/environment, uses them.
    Otherwise, generates and persists local keys to .vapid_keys.json.
    """
    if settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY:
        return settings.VAPID_PUBLIC_KEY, settings.VAPID_PRIVATE_KEY

    # Check local cache file
    if VAPID_CACHE_FILE.exists():
        try:
            with open(VAPID_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("public_key") and data.get("private_key"):
                    return data["public_key"], data["private_key"]
        except Exception as e:
            logger.warning(f"Failed to read cached VAPID keys: {e}")

    # Generate new VAPID keypair
    vapid = Vapid()
    vapid.generate_keys()
    
    # Export public key as URL-safe base64 string for browser PushManager
    import base64
    from cryptography.hazmat.primitives import serialization

    raw_bytes = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64_str = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")
    priv_pem = vapid.private_pem().decode("utf-8")


    try:
        with open(VAPID_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "public_key": pub_b64_str,
                "private_key": priv_pem,
            }, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not persist generated VAPID keys: {e}")

    return pub_b64_str, priv_pem


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
