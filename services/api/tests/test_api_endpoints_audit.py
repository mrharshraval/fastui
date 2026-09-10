import pytest
from sqlalchemy import select
from datetime import datetime, timezone
from models.schema import (
    Business, Lead, Contact, Note, Task, Reminder,
    Outreach, Interaction, Activity, PipelineStage, User, ActivityType
)

@pytest.mark.asyncio
async def test_post_activity_creates_and_returns_201(auth_client, db_session):
    """
    Verifies that POST /v1/businesses/{business_id}/activities successfully creates
    and records an activity with 201 Created status code.
    """
    biz = Business(business_name="Smile Dental Studio", city="Kolkata", website="https://smilestudio.in")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    payload = {
        "type": "website_visited",
        "channel": "website",
        "outcome": "Website visited",
        "notes": "https://smilestudio.in"
    }

    res = await auth_client.post(f"/v1/businesses/{biz.id}/activities", json=payload)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"

    data = res.json()
    assert data["business_id"] == biz.id
    assert data["type"] == "website_visited"
    assert data["channel"] == "website"
    assert data["outcome"] == "Website visited"
    assert data["notes"] == "https://smilestudio.in"
    assert data["id"] is not None

    # Verify activity exists in DB and GET /v1/businesses/{id}/activities returns it
    get_res = await auth_client.get(f"/v1/businesses/{biz.id}/activities")
    assert get_res.status_code == 200
    acts = get_res.json()
    assert any(a["id"] == data["id"] for a in acts)


@pytest.mark.asyncio
async def test_get_businesses_vs_get_leads(auth_client, db_session):
    """
    Verifies that GET /v1/leads returns only businesses with an active pipeline Lead,
    while GET /v1/businesses returns all business accounts (both prospects and leads).
    """
    # 1. Create a raw prospect business (no Lead record)
    biz_prospect = Business(business_name="Uncontacted Clinic", city="Delhi")
    db_session.add(biz_prospect)

    # 2. Create a pipeline lead business (with Lead record)
    biz_lead = Business(business_name="Active Lead Clinic", city="Mumbai")
    db_session.add(biz_lead)
    await db_session.commit()
    await db_session.refresh(biz_lead)
    await db_session.refresh(biz_prospect)

    lead = Lead(business_id=biz_lead.id, stage=PipelineStage.CONTACTED)
    db_session.add(lead)
    await db_session.commit()

    # GET /v1/leads should ONLY return biz_lead
    res_leads = await auth_client.get("/v1/leads?limit=500")
    assert res_leads.status_code == 200
    lead_ids = [b["id"] for b in res_leads.json()]
    assert biz_lead.id in lead_ids
    assert biz_prospect.id not in lead_ids

    # GET /v1/businesses should return BOTH accounts
    res_biz = await auth_client.get("/v1/businesses?limit=500")
    assert res_biz.status_code == 200
    all_ids = [b["id"] for b in res_biz.json()]
    assert biz_lead.id in all_ids
    assert biz_prospect.id in all_ids

    # Filter is_lead=true on /v1/businesses
    res_is_lead = await auth_client.get("/v1/businesses?is_lead=true&limit=500")
    assert res_is_lead.status_code == 200
    filtered_lead_ids = [b["id"] for b in res_is_lead.json()]
    assert biz_lead.id in filtered_lead_ids
    assert biz_prospect.id not in filtered_lead_ids


@pytest.mark.asyncio
async def test_pure_rest_lead_creation_and_mutations(auth_client, db_session):
    """
    Verifies:
    1. POST /v1/leads promotes a business to a Lead resource with 201 Created.
    2. PATCH /v1/leads bulk updates pipeline stage with 200 OK.
    3. PATCH /v1/prospects bulk updates qualification with 200 OK.
    4. PATCH /v1/businesses/{id} updates single stage / qualification with 200 OK.
    """
    biz1 = Business(business_name="Alpha Dental", city="Pune")
    biz2 = Business(business_name="Beta Dental", city="Goa")
    db_session.add_all([biz1, biz2])
    await db_session.commit()
    await db_session.refresh(biz1)
    await db_session.refresh(biz2)

    # 1. Single lead creation
    res_lead1 = await auth_client.post("/v1/leads", json={"business_id": biz1.id})
    assert res_lead1.status_code == 201
    data1 = res_lead1.json()
    assert data1["id"] == biz1.id
    assert data1["is_lead"] is True

    # 2. Bulk lead creation
    res_lead2 = await auth_client.post("/v1/leads", json={"business_ids": [biz2.id]})
    assert res_lead2.status_code == 201
    assert res_lead2.json()["added_count"] == 1

    # 3. Bulk stage update: PATCH /v1/leads
    res_stage = await auth_client.patch("/v1/leads", json={"business_ids": [biz1.id, biz2.id], "stage": "contacted"})
    assert res_stage.status_code == 200
    assert res_stage.json()["updated_count"] == 2

    # 4. Bulk qualify: PATCH /v1/prospects
    res_qual = await auth_client.patch("/v1/prospects", json={"business_ids": [biz1.id], "qualification_status": "qualified"})
    assert res_qual.status_code == 200

    # 5. Single resource update: PATCH /v1/businesses/{id}
    res_single = await auth_client.patch(f"/v1/businesses/{biz1.id}", json={"stage": "proposal"})
    assert res_single.status_code == 200
    assert res_single.json()["pipeline_stage"].lower() == "proposal"


@pytest.mark.asyncio
async def test_pure_rest_deletes_return_204_and_bulk_returns_200(auth_client, db_session):
    """
    Verifies:
    1. Single DELETE /v1/businesses/{id} returns 204 No Content with empty body.
    2. Single DELETE /v1/contacts/{id}, /notes/{id}, /reminders/{id}, /tasks/{id}, /activities/{id} return 204.
    3. Bulk DELETE /v1/businesses with body returns 200 OK.
    """
    biz = Business(business_name="Delete Target Clinic", city="Surat")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    # Sub-resources
    contact = Contact(business_id=biz.id, first_name="Dr.", last_name="Smith")
    note = Note(business_id=biz.id, user_id=1, content="Test Note")
    task = Task(business_id=biz.id, user_id=1, title="Call Clinic")
    reminder = Reminder(business_id=biz.id, user_id=1, title="Follow Up", due_at=datetime.now(timezone.utc))
    activity = Activity(business_id=biz.id, user_id=1, type=ActivityType.NOTE_ADDED, notes="Test")
    db_session.add_all([contact, note, task, reminder, activity])
    await db_session.commit()
    await db_session.refresh(contact)
    await db_session.refresh(note)
    await db_session.refresh(task)
    await db_session.refresh(reminder)
    await db_session.refresh(activity)

    # Test 204 deletes for sub-resources
    del_note = await auth_client.delete(f"/v1/notes/{note.id}")
    assert del_note.status_code == 204
    assert del_note.text == ""

    del_task = await auth_client.delete(f"/v1/tasks/{task.id}")
    assert del_task.status_code == 204
    assert del_task.text == ""

    del_rem = await auth_client.delete(f"/v1/reminders/{reminder.id}")
    assert del_rem.status_code == 204
    assert del_rem.text == ""

    del_act = await auth_client.delete(f"/v1/activities/{activity.id}")
    assert del_act.status_code == 204
    assert del_act.text == ""

    del_contact = await auth_client.delete(f"/v1/contacts/{contact.id}")
    assert del_contact.status_code == 204
    assert del_contact.text == ""

    # Test 204 single business delete
    del_biz = await auth_client.delete(f"/v1/businesses/{biz.id}")
    assert del_biz.status_code == 204
    assert del_biz.text == ""

    # Test bulk delete: DELETE /v1/businesses with body
    biz_a = Business(business_name="Bulk A")
    biz_b = Business(business_name="Bulk B")
    db_session.add_all([biz_a, biz_b])
    await db_session.commit()
    await db_session.refresh(biz_a)
    await db_session.refresh(biz_b)

    del_bulk = await auth_client.request("DELETE", "/v1/businesses", json={"business_ids": [biz_a.id, biz_b.id]})
    assert del_bulk.status_code == 200
    assert del_bulk.json()["deleted_count"] == 2


@pytest.mark.asyncio
async def test_legacy_and_alias_endpoints_return_404(auth_client):
    """
    Verifies that all removed legacy/verb/alias routes return 404 Not Found.
    """
    removed_routes = [
        ("GET", "/v1/follow-ups"),
        ("POST", "/v1/businesses/bulk-delete"),
        ("POST", "/v1/prospects/bulk-delete"),
        ("POST", "/v1/leads/bulk-delete"),
        ("POST", "/v1/leads/bulk-stage"),
        ("POST", "/v1/businesses/bulk-stage"),
        ("POST", "/v1/prospects/bulk-qualify"),
        ("POST", "/v1/prospects/1/add-to-leads"),
        ("POST", "/v1/prospects/bulk-add-to-leads"),
        ("PATCH", "/v1/businesses/1/stage"),
        ("PATCH", "/v1/leads/1/stage"),
        ("DELETE", "/v1/leads/1"),
        ("DELETE", "/v1/prospects/1"),
        # Unversioned paths must also return 404
        ("GET", "/businesses/1"),
        ("GET", "/prospects"),
        ("GET", "/leads"),
    ]

    for method, path in removed_routes:
        res = await auth_client.request(method, path, json={})
        assert res.status_code in (404, 405), f"Route {method} {path} should be 404 or 405, got {res.status_code}"


@pytest.mark.asyncio
async def test_auth_me_delete_returns_204(auth_client, db_session):
    """
    Verifies that DELETE /v1/auth/me completes account deletion and returns 204 No Content.
    """
    res = await auth_client.delete("/v1/auth/me")
    assert res.status_code == 204
    assert res.text == ""

    # Subsequent request with same credentials should be 401
    res_after = await auth_client.get("/v1/auth/me")
    assert res_after.status_code == 401


@pytest.mark.asyncio
async def test_exception_structured_envelope(auth_client):
    """
    Verifies that both FastUIException and standard HTTPException responses
    consistently include both 'detail' and the structured 'error' envelope
    with code, message, and request_id.
    """
    # 1. FastUIException (e.g. EntityNotFoundException on missing business)
    res_domain = await auth_client.get("/v1/businesses/99999999")
    assert res_domain.status_code == 404
    body_domain = res_domain.json()
    assert "detail" in body_domain
    assert "error" in body_domain
    assert body_domain["error"]["code"] == "NOT_FOUND"
    assert "Business" in body_domain["error"]["message"] or "not found" in body_domain["error"]["message"].lower()
    assert "request_id" in body_domain["error"]

    # 2. Standard HTTPException (e.g. invalid login credentials)
    res_http = await auth_client.post("/v1/auth/login", json={"email": "nonexistent@fastui.in", "password": "wrong"})
    assert res_http.status_code == 401
    body_http = res_http.json()
    assert "detail" in body_http
    assert "error" in body_http
    assert body_http["error"]["code"] == "HTTP_401"
    assert "Invalid email or password" in body_http["error"]["message"]
    assert "request_id" in body_http["error"]
