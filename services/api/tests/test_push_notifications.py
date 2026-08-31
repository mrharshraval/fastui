import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from main import app
from models.schema import User, UserRole, Business, Reminder, ReminderStatus, PushSubscription
from services.auth_service import create_access_token
from services.reminder_service import ReminderNotificationService
from unittest.mock import patch


@pytest.mark.asyncio
async def test_get_vapid_public_key(db_session: AsyncSession):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/notifications/vapid-public-key")
        assert res.status_code == 200
        data = res.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 20


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe_push_notifications(db_session: AsyncSession):
    # 1. Create a test user
    user = User(
        email="push_test@fastui.in",
        name="Push Tester",
        hashed_password="hashed_password",
        role=UserRole.SALES,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake-test-endpoint-123",
        "keys": {
            "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
            "auth": "tBHItJI5svbpez7KI4CCXg",
        },
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 2. Subscribe
        sub_res = await client.post("/notifications/subscribe", json=payload, headers=headers)
        assert sub_res.status_code == 200
        sub_data = sub_res.json()
        assert sub_data["endpoint"] == payload["endpoint"]

        # Verify in DB
        db_sub_res = await db_session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == payload["endpoint"])
        )
        db_sub = db_sub_res.scalar_one_or_none()
        assert db_sub is not None
        assert db_sub.user_id == user.id

        # 3. Test push
        with patch("services.push_service.PushNotificationService.send_notification", return_value=True) as mock_send:
            test_res = await client.post(
                "/notifications/test",
                json={"title": "Test Alert", "body": "Testing Web Push"},
                headers=headers,
            )
            assert test_res.status_code == 200
            assert test_res.json()["status"] == "sent"
            assert mock_send.called

        # 4. Unsubscribe
        unsub_res = await client.delete(
            f"/notifications/unsubscribe?endpoint={payload['endpoint']}",
            headers=headers,
        )
        assert unsub_res.status_code == 200

        # Verify removed from DB
        db_sub_res = await db_session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == payload["endpoint"])
        )
        assert db_sub_res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_reminder_notification_dispatch_and_status_update(db_session: AsyncSession):
    # 1. Create user, business, reminder, and push subscription
    user = User(
        email="reminder_user@fastui.in",
        name="Reminder User",
        hashed_password="hashed_password",
        role=UserRole.SALES,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    business = Business(
        business_name="Acme Dental",
        category="Dental Clinics",
        qualification_status="unqualified",
    )
    db_session.add(business)
    await db_session.flush()

    past_due = datetime.now(timezone.utc) - timedelta(minutes=5)
    reminder = Reminder(
        business_id=business.id,
        user_id=user.id,
        title="Follow up with Dr. Smith",
        notes="Discuss annual subscription",
        due_at=past_due,
        status=ReminderStatus.PENDING,
    )
    db_session.add(reminder)

    sub = PushSubscription(
        user_id=user.id,
        endpoint="https://updates.push.apple.com/wps/v1/fake-apple-endpoint",
        p256dh="BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
        auth="tBHItJI5svbpez7KI4CCXg",
    )
    db_session.add(sub)
    await db_session.commit()

    # 2. Process due reminders
    with patch("services.push_service.PushNotificationService.send_notification", return_value=True) as mock_send:
        processed = await ReminderNotificationService.process_due_reminders(db_session)
        assert processed == 1
        assert mock_send.called

        # 3. Verify notification_sent_at is set
        await db_session.refresh(reminder)
        assert reminder.notification_sent_at is not None

        # 4. Running again should process 0 (already notified)
        mock_send.reset_mock()
        processed_again = await ReminderNotificationService.process_due_reminders(db_session)
        assert processed_again == 0
        assert not mock_send.called
