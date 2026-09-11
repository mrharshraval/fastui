import pytest

from app.domains.models import (
    Activity,
    ActivityType,
    Business,
    BusinessSource,
    Lead,
    PushSubscription,
    User,
    UserRole,
)
from app.shared.security import create_access_token, get_password_hash


async def _create_user(db, email, name=None):
    role = UserRole.SALES
    u = User(
        email=email,
        name=name,
        hashed_password=get_password_hash("password"),
        role=role,
        is_active=True,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def _auth(client, user):
    role_val = user.role.value if hasattr(user.role, "value") else user.role
    token = create_access_token({"user_id": user.id, "email": user.email, "role": role_val})
    client.cookies.set("access_token", token)
    return client


async def _biz(db, name):
    b = Business(business_name=name)
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


@pytest.mark.asyncio
async def test_login_sets_cookie(client, db_session):
    await _create_user(db_session, "alice@fastui.in")
    res = await client.post(
        "/v1/auth/login", json={"email": "alice@fastui.in", "password": "password"}
    )
    assert res.status_code == 200
    assert "access_token" in res.cookies


@pytest.mark.asyncio
async def test_logout_status(client, db_session):
    await _create_user(db_session, "alice@fastui.in")
    await client.post("/v1/auth/login", json={"email": "alice@fastui.in", "password": "password"})
    res = await client.post("/v1/auth/logout", json={})
    assert res.status_code == 200
    assert res.json()["status"] == "logged out"


@pytest.mark.asyncio
async def test_me_unauthenticated_401(client):
    assert (await client.get("/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_401(client):
    client.cookies.set("access_token", "not.a.real.jwt")
    assert (await client.get("/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_401(client, db_session):
    u = User(
        email="inactive@fastui.in",
        hashed_password=get_password_hash("password"),
        role=UserRole.SALES,
        is_active=False,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    token = create_access_token({"user_id": u.id, "email": u.email, "role": "sales"})
    client.cookies.set("access_token", token)
    assert (await client.get("/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_nonexistent_user_jwt_401(client):
    token = create_access_token({"user_id": 999999, "email": "ghost@fastui.in", "role": "sales"})
    client.cookies.set("access_token", token)
    assert (await client.get("/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_protected_routes_all_401(client):
    for method, path in [
        ("GET", "/v1/businesses"),
        ("GET", "/v1/leads"),
        ("GET", "/v1/prospects"),
        ("GET", "/v1/tasks"),
        ("GET", "/v1/reminders"),
        ("GET", "/v1/activities"),
        ("GET", "/v1/stats"),
        ("GET", "/v1/auth/me"),
    ]:
        res = await client.request(method, path)
        assert res.status_code == 401, f"{method} {path} returned {res.status_code}"


@pytest.mark.asyncio
async def test_note_attributed_to_author(client, db_session):
    u = await _create_user(db_session, "alice@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, u)
    res = await client.post(f"/v1/businesses/{b.id}/notes", json={"content": "test"})
    assert res.status_code in (200, 201)
    assert res.json()["user_id"] == u.id


@pytest.mark.asyncio
async def test_task_attributed_to_author(client, db_session):
    u = await _create_user(db_session, "alice@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, u)
    res = await client.post(f"/v1/businesses/{b.id}/tasks", json={"title": "Task"})
    assert res.status_code in (200, 201)
    assert res.json()["user_id"] == u.id


@pytest.mark.asyncio
async def test_outreach_attributed_to_author(client, db_session):
    u = await _create_user(db_session, "alice@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, u)
    res = await client.post(
        f"/v1/businesses/{b.id}/outreach", json={"channel": "call", "recipient": "+91999"}
    )
    assert res.status_code in (200, 201)
    assert res.json()["user_id"] == u.id


@pytest.mark.asyncio
async def test_reminder_attributed_to_author(client, db_session):
    u = await _create_user(db_session, "alice@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, u)
    res = await client.post(
        f"/v1/businesses/{b.id}/reminders",
        json={"title": "Reminder", "due_at": "2030-01-01T10:00:00Z"},
    )
    assert res.status_code in (200, 201)
    assert res.json()["user_id"] == u.id


@pytest.mark.asyncio
async def test_activity_user_name_from_full_name(client, db_session):
    u = await _create_user(db_session, "alice@fastui.in", name="Alice Smith")
    b = await _biz(db_session, "ACME")
    _auth(client, u)
    await client.post(f"/v1/businesses/{b.id}/notes", json={"content": "note"})
    acts = (await client.get(f"/v1/businesses/{b.id}/activities")).json()
    note_act = next((a for a in acts if a.get("type") == "note_added"), None)
    assert note_act is not None
    assert note_act.get("user_name") == "Alice Smith"


@pytest.mark.asyncio
async def test_activity_user_name_from_email_prefix(client, db_session):
    u = await _create_user(db_session, "bobsmith@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, u)
    await client.post(f"/v1/businesses/{b.id}/notes", json={"content": "note"})
    acts = (await client.get(f"/v1/businesses/{b.id}/activities")).json()
    note_act = next((a for a in acts if a.get("type") == "note_added"), None)
    assert note_act is not None
    assert note_act.get("user_name") == "Bobsmith"


@pytest.mark.asyncio
async def test_tasks_scoped_to_user(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in")
    bob = await _create_user(db_session, "bob@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, alice)
    await client.post(f"/v1/businesses/{b.id}/tasks", json={"title": "Alice private"})
    _auth(client, bob)
    res = await client.get("/v1/tasks")
    assert res.status_code == 200
    assert "Alice private" not in [t["title"] for t in res.json()]


@pytest.mark.asyncio
async def test_reminders_scoped_to_user(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in")
    bob = await _create_user(db_session, "bob@fastui.in")
    b = await _biz(db_session, "ACME")
    _auth(client, alice)
    await client.post(
        f"/v1/businesses/{b.id}/reminders",
        json={"title": "Alice private", "due_at": "2030-06-01T09:00:00Z"},
    )
    _auth(client, bob)
    res = await client.get("/v1/reminders")
    assert res.status_code == 200
    assert "Alice private" not in [r["title"] for r in res.json()]


@pytest.mark.asyncio
async def test_two_user_activity_attribution(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in", name="Alice")
    bob = await _create_user(db_session, "bob@fastui.in", name="Bob")
    b = await _biz(db_session, "Shared")
    _auth(client, alice)
    await client.post(f"/v1/businesses/{b.id}/notes", json={"content": "Alice note"})
    _auth(client, bob)
    await client.post(f"/v1/businesses/{b.id}/notes", json={"content": "Bob note"})
    _auth(client, alice)
    acts = (await client.get(f"/v1/businesses/{b.id}/activities")).json()
    names = {a.get("user_name") for a in acts}
    assert "Alice" in names
    assert "Bob" in names


@pytest.mark.asyncio
async def test_push_unsubscribe_scoped_to_user(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in")
    bob = await _create_user(db_session, "bob@fastui.in")
    sub = PushSubscription(
        user_id=alice.id, endpoint="https://push.example.com/alice", p256dh="k", auth="a"
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)
    _auth(client, bob)
    await client.delete(
        "/v1/notifications/unsubscribe", params={"endpoint": "https://push.example.com/alice"}
    )
    still = await db_session.get(PushSubscription, sub.id)
    assert still is not None


@pytest.mark.asyncio
async def test_logout_then_me_401(client, db_session):
    await _create_user(db_session, "alice@fastui.in")
    await client.post("/v1/auth/login", json={"email": "alice@fastui.in", "password": "password"})
    assert (await client.get("/v1/auth/me")).status_code == 200
    await client.post("/v1/auth/logout", json={})
    client.cookies.delete("access_token")
    assert (await client.get("/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_update_profile_persists_to_db(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in", name="Alice")
    _auth(client, alice)
    res = await client.patch("/v1/auth/me", json={"name": "Alice Smith"})
    assert res.status_code == 200
    assert res.json()["name"] == "Alice Smith"
    updated_user = await db_session.get(User, alice.id)
    assert updated_user.name == "Alice Smith"


@pytest.mark.asyncio
async def test_update_business_persists_to_db(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in")
    b = await _biz(db_session, "Old Corp")
    _auth(client, alice)
    res = await client.patch(
        f"/v1/businesses/{b.id}",
        json={
            "business_name": "New Corp",
            "phone": "+1234567890",
            "city": "San Francisco",
            "qualification_status": "qualified",
        },
    )
    assert res.status_code == 200
    assert res.json()["business_name"] == "New Corp"
    assert res.json()["city"] == "San Francisco"
    updated_b = await db_session.get(Business, b.id)
    assert updated_b.business_name == "New Corp"
    assert updated_b.city == "San Francisco"


@pytest.mark.asyncio
async def test_delete_business_persists_to_db(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in")
    b = await _biz(db_session, "Delete Me Corp")
    _auth(client, alice)
    res = await client.delete(f"/v1/businesses/{b.id}")
    assert res.status_code in (200, 204)
    deleted_b = await db_session.get(Business, b.id)
    assert deleted_b is None


@pytest.mark.asyncio
async def test_bulk_delete_businesses_persists_to_db(client, db_session):
    alice = await _create_user(db_session, "alice@fastui.in")
    b1 = await _biz(db_session, "Bulk 1")
    b2 = await _biz(db_session, "Bulk 2")
    _auth(client, alice)
    res = await client.request("DELETE", "/v1/businesses", json={"business_ids": [b1.id, b2.id]})
    assert res.status_code == 200
    assert res.json()["deleted_count"] == 2
    assert (await db_session.get(Business, b1.id)) is None
    assert (await db_session.get(Business, b2.id)) is None


@pytest.mark.asyncio
async def test_delete_business_with_relations(client, db_session):
    alice = await _create_user(db_session, "alice2@fastui.in")
    b = await _biz(db_session, "Delete With Relations Corp")

    src = BusinessSource(business_id=b.id, platform="google_maps", external_id="ext_test_123")
    db_session.add(src)
    act = Activity(business_id=b.id, type=ActivityType.BUSINESS_DISCOVERED)
    db_session.add(act)
    lead = Lead(business_id=b.id)
    db_session.add(lead)
    await db_session.commit()

    _auth(client, alice)
    res = await client.delete(f"/v1/businesses/{b.id}")
    assert res.status_code in (200, 204), res.text
    assert (await db_session.get(Business, b.id)) is None
