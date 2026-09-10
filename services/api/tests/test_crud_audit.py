import pytest
from sqlalchemy import select
from datetime import datetime, timezone
from models.schema import (
    Business, Lead, Contact, Note, Task, Reminder,
    Outreach, Interaction, Activity, ProspectDemo, CrawledWebsite,
    PipelineStage, ActivityType, OutreachChannel, OutreachStatus, User
)

@pytest.mark.asyncio
async def test_single_business_cascade_deletion(auth_client, db_session):
    # Create business
    biz = Business(business_name="Dental Clinic Alpha", city="Kolkata")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    # Attach lead
    lead = Lead(business_id=biz.id, stage=PipelineStage.LEAD)
    db_session.add(lead)

    # Attach contact
    contact = Contact(business_id=biz.id, first_name="Dr. John", last_name="Doe", email="john@alpha.com")
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    # Attach note, task, reminder, activity, outreach, demo
    note = Note(business_id=biz.id, content="Important note")
    task = Task(business_id=biz.id, title="Follow up task")
    reminder = Reminder(business_id=biz.id, title="Check in", due_at=datetime.now(timezone.utc))
    activity = Activity(business_id=biz.id, type=ActivityType.CALL_INITIATED, channel="phone")
    outreach = Outreach(business_id=biz.id, channel=OutreachChannel.CALL, status=OutreachStatus.CONNECTED, recipient="+919876543210")
    demo = ProspectDemo(business_id=biz.id, token="token-123456789012345678")
    db_session.add_all([note, task, reminder, activity, outreach, demo])
    await db_session.commit()

    # Delete via API: 204 No Content
    res = await auth_client.delete(f"/v1/businesses/{biz.id}")
    assert res.status_code == 204
    assert res.text == ""

    # Verify parent business is gone
    biz_check = await db_session.get(Business, biz.id)
    assert biz_check is None

    # Verify children are gone
    leads = (await db_session.execute(select(Lead).where(Lead.business_id == biz.id))).scalars().all()
    assert len(leads) == 0

    contacts = (await db_session.execute(select(Contact).where(Contact.business_id == biz.id))).scalars().all()
    assert len(contacts) == 0

    notes = (await db_session.execute(select(Note).where(Note.business_id == biz.id))).scalars().all()
    assert len(notes) == 0


@pytest.mark.asyncio
async def test_bulk_delete_businesses(auth_client, db_session):
    b1 = Business(business_name="Clinic 1", city="Mumbai")
    b2 = Business(business_name="Clinic 2", city="Delhi")
    db_session.add_all([b1, b2])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)

    res = await auth_client.request("DELETE", "/v1/businesses", json={"business_ids": [b1.id, b2.id]})
    assert res.status_code == 200
    assert res.json()["deleted_count"] == 2

    assert await db_session.get(Business, b1.id) is None
    assert await db_session.get(Business, b2.id) is None


@pytest.mark.asyncio
async def test_bulk_qualify_prospects(auth_client, db_session):
    b1 = Business(business_name="Prospect 1", qualification_status="unqualified")
    b2 = Business(business_name="Prospect 2", qualification_status="unqualified")
    db_session.add_all([b1, b2])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)

    res = await auth_client.patch("/v1/prospects", json={
        "business_ids": [b1.id, b2.id],
        "qualification_status": "qualified"
    })
    assert res.status_code == 200
    assert res.json()["updated_count"] == 2

    await db_session.refresh(b1)
    await db_session.refresh(b2)
    assert b1.qualification_status == "qualified"
    assert b2.qualification_status == "qualified"


@pytest.mark.asyncio
async def test_bulk_update_stage(auth_client, db_session):
    b1 = Business(business_name="Lead 1")
    b2 = Business(business_name="Lead 2")
    db_session.add_all([b1, b2])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)

    l1 = Lead(business_id=b1.id, stage=PipelineStage.LEAD)
    l2 = Lead(business_id=b2.id, stage=PipelineStage.LEAD)
    db_session.add_all([l1, l2])
    await db_session.commit()

    res = await auth_client.patch("/v1/leads", json={
        "business_ids": [b1.id, b2.id],
        "stage": "contacted"
    })
    assert res.status_code == 200
    assert res.json()["updated_count"] == 2

    await db_session.refresh(l1)
    await db_session.refresh(l2)
    assert l1.stage == PipelineStage.CONTACTED
    assert l2.stage == PipelineStage.CONTACTED


@pytest.mark.asyncio
async def test_contacts_crud(auth_client, db_session):
    biz = Business(business_name="Enterprise Corp")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    c = Contact(business_id=biz.id, first_name="Sarah", last_name="Connor", email="sarah@corp.com", role="CTO")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    # List contacts
    res = await auth_client.get("/v1/contacts")
    assert res.status_code == 200
    contacts = res.json()
    assert len(contacts) >= 1
    target = next((item for item in contacts if item["email"] == "sarah@corp.com"), None)
    assert target is not None
    assert target["name"] == "Sarah Connor"
    assert target["company_name"] == "Enterprise Corp"

    # Delete contact: 204 No Content
    del_res = await auth_client.delete(f"/v1/contacts/{c.id}")
    assert del_res.status_code == 204
    assert del_res.text == ""

    # Verify deleted
    assert await db_session.get(Contact, c.id) is None


@pytest.mark.asyncio
async def test_activity_deletion(auth_client, db_session):
    biz = Business(business_name="Demo Biz")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    act = Activity(business_id=biz.id, type=ActivityType.NOTE_ADDED, notes="Test note")
    db_session.add(act)
    await db_session.commit()
    await db_session.refresh(act)

    # Delete activity: 204 No Content
    res = await auth_client.delete(f"/v1/activities/{act.id}")
    assert res.status_code == 204
    assert res.text == ""

    assert await db_session.get(Activity, act.id) is None


@pytest.mark.asyncio
async def test_auth_delete_me(auth_client, db_session):
    # Delete me: 204 No Content
    res = await auth_client.delete("/v1/auth/me")
    assert res.status_code == 204
    assert res.text == ""

    # Subsequent call to /auth/me should now be 401 Unauthorized
    me_res = await auth_client.get("/v1/auth/me")
    assert me_res.status_code == 401
