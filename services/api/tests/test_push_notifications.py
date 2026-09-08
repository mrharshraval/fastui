import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from main import app
from models.schema import User, UserRole, Business, Reminder, ReminderStatus, PushSubscription
from services.auth_service import create_access_token
from services.push_service import PushNotificationService
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


@pytest.mark.asyncio
async def test_broadcast_to_user_deduplication(db_session: AsyncSession):
    # 1. Create a test user
    user = User(
        email="multi_device@fastui.in",
        name="Multi Device User",
        hashed_password="hashed_password",
        role=UserRole.SALES,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # 2. Add 2 unique devices and 1 device with corrupt/missing crypto keys
    sub1 = PushSubscription(
        user_id=user.id,
        endpoint="https://fcm.googleapis.com/fcm/send/device-phone-1",
        p256dh="key1",
        auth="auth1",
    )
    sub2 = PushSubscription(
        user_id=user.id,
        endpoint="https://updates.push.apple.com/wps/v1/device-laptop-2",
        p256dh="key2",
        auth="auth2",
    )
    sub3_corrupt = PushSubscription(
        user_id=user.id,
        endpoint="https://fcm.googleapis.com/fcm/send/device-corrupt-3",
        p256dh="",  # empty/corrupt key
        auth="auth3",
    )
    db_session.add_all([sub1, sub2, sub3_corrupt])
    await db_session.commit()

    called_endpoints = []

    def mock_send(sub_info, payload, ttl=86400):
        called_endpoints.append(sub_info["endpoint"])
        return True

    with patch("services.push_service.PushNotificationService.send_notification", side_effect=mock_send):
        metrics = await PushNotificationService.broadcast_to_user(
            session=db_session,
            user_id=user.id,
            payload={"title": "Team Alert", "body": "Meeting at 3 PM"},
        )

        assert metrics["total_subscriptions"] == 3
        assert metrics["unique_devices"] == 2
        assert metrics["dispatched_devices"] == 2
        assert metrics["failed_devices"] == 0
        assert metrics["cleaned_up_devices"] == 1  # corrupt device cleaned up

        # Verify only 2 unique valid devices were called and no duplicate calls were made
        assert len(called_endpoints) == 2
        assert set(called_endpoints) == {sub1.endpoint, sub2.endpoint}



@pytest.mark.asyncio
async def test_broadcast_stale_device_cleanup(db_session: AsyncSession):
    # 1. Create user with 1 active device and 1 expired device
    user = User(
        email="stale_cleanup@fastui.in",
        name="Stale Device User",
        hashed_password="hashed_password",
        role=UserRole.SALES,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    active_sub = PushSubscription(
        user_id=user.id,
        endpoint="https://fcm.googleapis.com/fcm/send/active-phone",
        p256dh="active_p256dh",
        auth="active_auth",
    )
    expired_sub = PushSubscription(
        user_id=user.id,
        endpoint="https://fcm.googleapis.com/fcm/send/expired-tablet",
        p256dh="expired_p256dh",
        auth="expired_auth",
    )
    db_session.add_all([active_sub, expired_sub])
    await db_session.commit()

    def mock_send_with_expiry(sub_info, payload, ttl=86400):
        if "expired" in sub_info["endpoint"]:
            return False  # simulates 410 Gone / 404 Not Found
        return True

    with patch("services.push_service.PushNotificationService.send_notification", side_effect=mock_send_with_expiry):
        metrics = await PushNotificationService.broadcast_to_user(
            session=db_session,
            user_id=user.id,
            payload={"title": "Test", "body": "Checking cleanup"},
        )

        assert metrics["unique_devices"] == 2
        assert metrics["dispatched_devices"] == 1
        assert metrics["failed_devices"] == 1
        assert metrics["cleaned_up_devices"] == 1

        # Verify expired subscription was deleted from DB while active subscription remains
        res = await db_session.execute(
            select(PushSubscription).where(PushSubscription.user_id == user.id)
        )
        remaining_subs = list(res.scalars().all())
        assert len(remaining_subs) == 1
        assert remaining_subs[0].endpoint == active_sub.endpoint


@pytest.mark.asyncio
async def test_broadcast_api_route(db_session: AsyncSession):
    user = User(
        email="broadcast_route@fastui.in",
        name="Broadcast Tester",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    sub = PushSubscription(
        user_id=user.id,
        endpoint="https://fcm.googleapis.com/fcm/send/route-test-phone",
        p256dh="route_p256dh",
        auth="route_auth",
    )
    db_session.add(sub)
    await db_session.commit()

    token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    with patch("services.push_service.PushNotificationService.send_notification", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(
                "/notifications/broadcast",
                json={
                    "title": "System Update",
                    "body": "New leads uploaded for today.",
                    "url": "/prospects",
                },
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "sent"
            assert data["user_id"] == user.id
            assert data["dispatched_devices"] == 1
            assert data["unique_devices"] == 1
            assert data["cleaned_up_devices"] == 0


@pytest.mark.asyncio
async def test_broadcast_to_all_accounts_endpoint(db_session: AsyncSession):
    user1 = User(
        email="admin_all@fastui.in",
        name="Admin One",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
    )
    user2 = User(
        email="sales_all@fastui.in",
        name="Sales Two",
        hashed_password="hashed_password",
        role=UserRole.SALES,
        is_active=True,
    )
    db_session.add_all([user1, user2])
    await db_session.flush()

    sub1 = PushSubscription(
        user_id=user1.id,
        endpoint="https://fcm.googleapis.com/fcm/send/admin-phone-all",
        p256dh="key1",
        auth="auth1",
    )
    sub2 = PushSubscription(
        user_id=user2.id,
        endpoint="https://fcm.googleapis.com/fcm/send/sales-phone-all",
        p256dh="key2",
        auth="auth2",
    )
    db_session.add_all([sub1, sub2])
    await db_session.commit()

    token = create_access_token(data={"sub": user1.email, "user_id": user1.id, "role": user1.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    with patch("services.push_service.PushNotificationService.send_notification", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(
                "/notifications/broadcast",
                json={
                    "all_accounts": True,
                    "title": "Company-wide Announcement",
                    "body": "All hands meeting in 10 minutes.",
                },
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "sent"
            assert data["dispatched_devices"] >= 2
            assert data["unique_devices"] >= 2


