"""FastUI Notifications Domain."""

from app.domains.notifications.models import PushSubscription
from app.domains.notifications.service import NotificationService

__all__ = ["NotificationService", "PushSubscription"]
