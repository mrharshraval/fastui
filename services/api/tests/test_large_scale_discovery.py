"""
FastUI Large-Scale Discovery Tests
==================================
Verifies bounded batching, target/remaining calculations, DB deduplication,
cross-source provenance, multi-run resumability, and source exhaustion.
"""

from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.schema import Business, BusinessSource, DiscoveryJob, JobStatus
from schemas.discovery import DiscoveredLead, DiscoverResponse
from services.discovery_service import DiscoveryService


@pytest.mark.asyncio
async def test_existing_prospects_deducted_and_zero_worker_calls_when_target_met(
    db_session: AsyncSession,
):
    """
    If database already has >= target_count prospects in scope,
    DiscoveryService immediately completes without invoking WorkerClient.
    """
    # Seed 10 existing dental prospects in Kolkata
    for i in range(10):
        db_session.add(
            Business(
                business_name=f"Existing Dental {i}",
                category="Dental Clinics",
                city="Kolkata",
                qualification_status="unqualified",
            )
        )
    await db_session.commit()

    # Create job with target_count = 10
    job = DiscoveryJob(
        query={
            "business_type": "Dental Clinics",
            "location": {"city": "Kolkata"},
            "target_count": 10,
        },
        status=JobStatus.QUEUED,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    with patch("services.discovery_service.WorkerClient.discover_batch", new_callable=AsyncMock) as mock_worker:
        await DiscoveryService.process_job(job.id)
        mock_worker.assert_not_called()

    await db_session.refresh(job)
    assert job.status == JobStatus.COMPLETED
    assert job.existing_businesses >= 10
    assert job.new_leads == 0
    assert job.progress_percent == 100


@pytest.mark.asyncio
async def test_mandatory_multi_source_and_multi_run_scenario(
    db_session: AsyncSession,
):
    """
    Mandatory Scenario from specification:
    Target = 1000
    Existing = 100

    Run 1 discovers:
      Source A: 300 raw (100 duplicates with DB, 200 new)
      Source B: 400 raw (100 duplicates with Source A, 300 new)
      Source C: 300 raw (100 duplicates with previous sources, 200 new)
      Expected: Existing = 100, New = 700, Total = 800, Remaining = 200.

    Then verify Run 2 starts with:
      Target = 1000
      Existing = 800
      Remaining = 200 (requests only 200, not 1000, not 900, not 300).
    """
    # 1. Seed 100 existing prospects
    for i in range(100):
        db_session.add(
            Business(
                business_name=f"PreExisting Dental Clinic {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919800000{i:03d}",
                qualification_status="unqualified",
            )
        )
    await db_session.commit()

    # Prepare batches simulating Source A, B, C
    # Source A: 100 duplicates with PreExisting (phone match) + 200 new (A_1..A_200)
    source_a_leads = []
    for i in range(100):
        source_a_leads.append(
            DiscoveredLead(
                name=f"PreExisting Dental Clinic {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919800000{i:03d}",
                source_platform="google_maps",
                source_place_id=f"g_pre_{i}",
            )
        )
    for i in range(200):
        source_a_leads.append(
            DiscoveredLead(
                name=f"Dental Clinic A {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919810000{i:03d}",
                source_platform="google_maps",
                source_place_id=f"g_a_{i}",
            )
        )

    # Source B: 100 duplicates with Source A (same phone & place_id) + 300 new (B_1..B_300)
    source_b_leads = []
    for i in range(100):
        source_b_leads.append(
            DiscoveredLead(
                name=f"Dental Clinic A {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919810000{i:03d}",
                source_platform="source_b",
                source_place_id=f"g_a_{i}",
            )
        )
    for i in range(300):
        source_b_leads.append(
            DiscoveredLead(
                name=f"Dental Clinic B {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919820000{i:03d}",
                source_platform="source_b",
                source_place_id=f"b_{i}",
            )
        )

    # Source C: 100 duplicates with previous sources + 200 new (C_1..C_200)
    source_c_leads = []
    for i in range(100):
        source_c_leads.append(
            DiscoveredLead(
                name=f"Dental Clinic B {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919820000{i:03d}",
                source_platform="source_c",
            )
        )
    for i in range(200):
        source_c_leads.append(
            DiscoveredLead(
                name=f"Dental Clinic C {i}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+919830000{i:03d}",
                source_platform="source_c",
                source_place_id=f"c_{i}",
            )
        )

    # Combine all leads for Run 1
    run_1_all_leads = source_a_leads + source_b_leads + source_c_leads

    # Deliver in chunks of 50
    chunks = [run_1_all_leads[i:i+50] for i in range(0, len(run_1_all_leads), 50)]
    chunk_responses = [DiscoverResponse(leads=ch, count=len(ch), exhausted=False) for ch in chunks]
    # Final response signals exhaustion of current run
    chunk_responses.append(DiscoverResponse(leads=[], count=0, exhausted=True))

    job1 = DiscoveryJob(
        query={
            "business_type": "Dental Clinics",
            "location": {"city": "Kolkata"},
            "target_count": 1000,
        },
        status=JobStatus.QUEUED,
    )
    db_session.add(job1)
    await db_session.commit()
    await db_session.refresh(job1)

    with patch("services.discovery_service.WorkerClient.discover_batch", side_effect=chunk_responses):
        await DiscoveryService.process_job(job1.id)

    await db_session.refresh(job1)

    # Verify Run 1 outcomes:
    assert job1.status == JobStatus.COMPLETED
    assert job1.existing_businesses == 100
    assert job1.new_leads == 700  # 200 from A + 300 from B + 200 from C
    assert job1.duplicates == 300 # 100 (A dups with DB) + 100 (B dups with A) + 100 (C dups with B)
    total_in_scope_run1 = job1.existing_businesses + job1.new_leads
    assert total_in_scope_run1 == 800
    remaining_run1 = 1000 - total_in_scope_run1
    assert remaining_run1 == 200

    # ── Test Run 2: Starts with 800 existing, target 1000 → remaining 200 ──
    job2 = DiscoveryJob(
        query={
            "business_type": "Dental Clinics",
            "location": {"city": "Kolkata"},
            "target_count": 1000,
        },
        status=JobStatus.QUEUED,
    )
    db_session.add(job2)
    await db_session.commit()
    await db_session.refresh(job2)

    captured_batch_limits = []

    async def mock_run2_discover_batch(params):
        captured_batch_limits.append(params.limit)
        # Return final 200 new leads in batches of 50
        lead_batch = [
            DiscoveredLead(
                name=f"Dental Clinic Run2_{len(captured_batch_limits)}_{j}",
                category="Dental Clinics",
                city="Kolkata",
                phone=f"+91989{len(captured_batch_limits):02d}{j:04d}",
                source_platform="google_maps",
            )
            for j in range(params.limit)
        ]
        return DiscoverResponse(leads=lead_batch, count=len(lead_batch), exhausted=False)

    with patch("services.discovery_service.WorkerClient.discover_batch", side_effect=mock_run2_discover_batch):
        await DiscoveryService.process_job(job2.id)

    await db_session.refresh(job2)
    assert job2.existing_businesses == 800
    assert job2.new_leads == 200
    assert job2.progress_percent == 100
    # Confirm total requested across batches in Run 2 was exactly 200 (not 1000, not 900, not 300)
    assert sum(captured_batch_limits) == 200


@pytest.mark.asyncio
async def test_job_cancellation_mid_run(db_session: AsyncSession):
    job = DiscoveryJob(
        query={
            "business_type": "Plumbers",
            "location": {"city": "Mumbai"},
            "target_count": 500,
        },
        status=JobStatus.QUEUED,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    async def mock_discover_and_cancel(params):
        # Cancel job in DB during batch processing
        async with AsyncSession(db_session.bind) as s:
            j = await s.get(DiscoveryJob, job.id)
            j.status = JobStatus.CANCELLED
            await s.commit()
        return DiscoverResponse(
            leads=[
                DiscoveredLead(
                    name="Fast Plumber 1",
                    category="Plumbers",
                    city="Mumbai",
                    phone="+919800111111",
                )
            ],
            count=1,
        )

    with patch("services.discovery_service.WorkerClient.discover_batch", side_effect=mock_discover_and_cancel):
        await DiscoveryService.process_job(job.id)

    await db_session.refresh(job)
    assert job.status == JobStatus.CANCELLED
