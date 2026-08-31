import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.schema import Reminder, ReminderStatus, PushSubscription, Business
from services.push_service import PushNotificationService

logger = logging.getLogger(__name__)


class ReminderNotificationService:
    """
    Service responsible for checking due sales reminders and dispatching
    native phone push notifications.
    """

    @classmethod
    async def process_due_reminders(cls, session: AsyncSession) -> int:
        """
        Scans for all pending reminders that are past their due_at timestamp
        and have not yet had a notification sent.
        Dispatches push notifications and marks notification_sent_at.
        Returns the number of reminders processed.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch pending due reminders
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.business), selectinload(Reminder.user))
            .where(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.due_at <= now,
                Reminder.notification_sent_at.is_(None),
            )
            .order_by(Reminder.due_at.asc())
            .limit(50)
        )
        result = await session.execute(stmt)
        due_reminders: List[Reminder] = list(result.scalars().all())

        if not due_reminders:
            return 0

        logger.info(f"Found {len(due_reminders)} due reminders to notify.")
        processed_count = 0

        for reminder in due_reminders:
            user_id = reminder.user_id
            biz_name = reminder.business.business_name if reminder.business else "FastUI Sales"

            # 2. Fetch user's registered push subscriptions (if user assigned, or all users if unassigned)
            sub_stmt = select(PushSubscription)
            if user_id:
                sub_stmt = sub_stmt.where(PushSubscription.user_id == user_id)
            
            sub_res = await session.execute(sub_stmt)
            subscriptions = list(sub_res.scalars().all())

            payload = {
                "title": f"Reminder: {biz_name}",
                "body": reminder.title + (f" · {reminder.notes}" if reminder.notes else ""),
                "icon": "/assets/brand/favicon/brand/primary/filled.png",
                "badge": "/assets/brand/favicon/brand/primary/filled.png",
                "data": {
                  "url": f"/prospects",
                  "business_id": reminder.business_id,
                  "reminder_id": reminder.id,
                }
            }

            # 3. Dispatch to all devices
            for sub in subscriptions:
                sub_info = {
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    }
                }
                success = PushNotificationService.send_notification(sub_info, payload)
                if not success:
                    # Stale / expired subscription — clean up
                    await session.delete(sub)

            # 4. Mark reminder as notified
            reminder.notification_sent_at = datetime.now(timezone.utc)
            processed_count += 1

        await session.commit()
        return processed_count
