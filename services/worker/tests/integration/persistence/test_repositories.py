"""
Integration tests for persistence repositories.
Validates DiscoveryRepository and EnrichmentRepository against an in-memory SQLite database.
"""

from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from contracts.discovery import DiscoveredLead
from contracts.enrichment import (
    EnrichedBrand,
    EnrichedBusinessProfile,
    EnrichedContact,
    EnrichedDoctor,
)
from persistence.models import (
    Base,
    Business,
    BusinessSource,
    DiscoveryJob,
    DiscoveryTask,
    JobStatus,
    TaskStatus,
)
from persistence.repositories.discovery import DiscoveryRepository
from persistence.repositories.enrichment import EnrichmentRepository


@pytest.fixture
async def async_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_discovery_repository_lifecycle_and_batch_persistence(async_session: AsyncSession):
    repo = DiscoveryRepository(async_session)

    # 1. Create Job and Task
    job = DiscoveryJob(
        status=JobStatus.RUNNING,
        query={"target_audience": "Dentist", "limit": 10},
    )
    async_session.add(job)
    await async_session.commit()
    await async_session.refresh(job)

    task = DiscoveryTask(
        job_id=job.id,
        status=TaskStatus.PENDING,
        params={"target_audience": "Dentist", "location": "Ahmedabad"},
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)

    # 2. Update task status
    await repo.update_task_status(task.id, TaskStatus.RUNNING)
    refreshed_task = await repo.get_task(task.id)
    assert refreshed_task.status == TaskStatus.RUNNING
    assert refreshed_task.attempts == 1

    # 3. Persist leads batch (1 new, then same lead again -> duplicate)
    lead = DiscoveredLead(
        name="Apex Dental Care",
        category="Dentist",
        city="Ahmedabad",
        phone="+919876543210",
        website="https://apexdental.com",
        source_platform="google_maps",
        source_place_id="place_apex_1",
    )

    new_count, dup_count = await repo.persist_leads_batch(job.id, task.id, [lead])
    assert new_count == 1
    assert dup_count == 0

    # Persist duplicate lead
    new_count2, dup_count2 = await repo.persist_leads_batch(job.id, task.id, [lead])
    assert new_count2 == 0
    assert dup_count2 == 1

    # 4. Update job progress
    await repo.update_job_progress(job.id, new_leads=1, duplicates=1, is_exhausted=True)
    refreshed_job = await repo.get_job(job.id)
    assert refreshed_job.new_leads == 1
    assert refreshed_job.duplicates == 1
    assert refreshed_job.status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_enrichment_repository_save_result(async_session: AsyncSession):
    disc_repo = DiscoveryRepository(async_session)
    enrich_repo = EnrichmentRepository(async_session)

    lead = DiscoveredLead(
        name="Smile Studio",
        category="Dentist",
        city="Ahmedabad",
        website="https://smilestudio.com",
        source_platform="google_maps",
        source_place_id="place_smile_1",
    )
    biz, is_new = await disc_repo.persist_lead(job_id=1, lead=lead)
    await async_session.commit()
    assert is_new is True

    profile = EnrichedBusinessProfile(
        website_url="https://smilestudio.com",
        brand=EnrichedBrand(brand_name="Smile Studio Elite", logo_url="https://smilestudio.com/logo.png"),
        primary_doctor=EnrichedDoctor(name="Dr. Smith"),
        contact=EnrichedContact(emails=["hello@smilestudio.com"], phones=["+919898989898"], whatsapp="+919898989898"),
    )

    crawled = await enrich_repo.save_enrichment_result(biz.id, profile)
    assert crawled.domain == "smilestudio.com"
    assert biz.canonical_name == "Smile Studio Elite"
    assert biz.email == "hello@smilestudio.com"
    assert biz.has_whatsapp is True


@pytest.mark.asyncio
async def test_business_source_created_at_is_populated_and_timezone_aware(async_session: AsyncSession):
    """
    Regression Test 1:
    Verifies that BusinessSource automatically populates created_at and last_seen_at
    with timezone-aware UTC datetimes when omitted.
    """
    biz = Business(
        canonical_name="Test Dental",
        source_name="Test Dental",
        business_name="Test Dental",
        raw_business_name="Test Dental",
        normalized_business_name="test dental",
        source_platform="google_maps",
    )
    async_session.add(biz)
    await async_session.flush()

    source = BusinessSource(
        business_id=biz.id,
        platform="google_maps",
        external_id="ext_test_123",
        source_url="https://google.com/maps?cid=123",
    )
    async_session.add(source)
    await async_session.flush()

    assert source.created_at is not None
    assert source.last_seen_at is not None
    # Model defaults populate timezone-aware UTC datetime
    assert source.created_at.tzinfo is not None
    assert source.last_seen_at.tzinfo is not None

    await async_session.commit()
    await async_session.refresh(source)
    assert source.created_at is not None
    assert source.last_seen_at is not None


@pytest.mark.asyncio
async def test_batch_persistence_savepoint_isolation_and_no_cascade(async_session: AsyncSession):
    """
    Regression Test 2:
    Verifies that if an individual record in a batch fails, only its savepoint rolls back.
    The session is NOT left in a poisoned PendingRollbackError state, and subsequent records
    in the batch are successfully persisted and committed.
    """
    repo = DiscoveryRepository(async_session)
    job = DiscoveryJob(status=JobStatus.RUNNING, query={"target_audience": "Dentist"})
    async_session.add(job)
    await async_session.commit()
    await async_session.refresh(job)

    lead1 = DiscoveredLead(
        name="Valid Clinic 1",
        category="Dentist",
        city="Mumbai",
        phone="+919811111111",
        website="https://clinic1.com",
        source_platform="google_maps",
        source_place_id="place_valid_1",
    )
    bad_lead = DiscoveredLead(
        name="Crashing Clinic 2",
        category="Dentist",
        city="Mumbai",
        phone="+919822222222",
        source_platform="google_maps",
        source_place_id="place_bad_2",
    )
    lead3 = DiscoveredLead(
        name="Valid Clinic 3",
        category="Dentist",
        city="Mumbai",
        phone="+919833333333",
        website="https://clinic3.com",
        source_platform="google_maps",
        source_place_id="place_valid_3",
    )

    original_persist_lead = repo.persist_lead

    async def flaky_persist_lead(j_id: int, lead_item: DiscoveredLead):
        if lead_item.name == "Crashing Clinic 2":
            raise RuntimeError("Simulated transient database/validation failure on bad_lead")
        return await original_persist_lead(j_id, lead_item)

    with patch.object(repo, "persist_lead", side_effect=flaky_persist_lead):
        new_count, dup_count = await repo.persist_leads_batch(
            job.id, task_id=1, leads=[lead1, bad_lead, lead3]
        )

    # lead1 and lead3 must succeed; bad_lead failure must not kill batch or poison session
    assert new_count == 2
    assert dup_count == 0

    # Verify both records exist in the database
    res = await async_session.execute(select(Business).order_by(Business.id))
    businesses = res.scalars().all()
    assert len(businesses) == 2
    b_names = {b.business_name for b in businesses}
    assert "Valid Clinic 1" in b_names
    assert "Valid Clinic 3" in b_names


@pytest.mark.asyncio
async def test_batch_persistence_rollback_on_commit_failure(async_session: AsyncSession):
    """
    Regression Test 3:
    Verifies that if commit() fails in persist_leads_batch, the session is explicitly rolled back
    and the exception is re-raised.
    """
    repo = DiscoveryRepository(async_session)
    job = DiscoveryJob(status=JobStatus.RUNNING, query={"target_audience": "Dentist"})
    async_session.add(job)
    await async_session.commit()
    await async_session.refresh(job)

    lead = DiscoveredLead(
        name="Fail Commit Clinic",
        category="Dentist",
        city="Delhi",
        phone="+919844444444",
        source_platform="google_maps",
        source_place_id="place_commit_fail_1",
    )

    with (
        patch.object(async_session, "commit", side_effect=RuntimeError("Simulated commit error")),
        patch.object(async_session, "rollback", wraps=async_session.rollback) as mock_rollback,
    ):
        with pytest.raises(RuntimeError, match="Simulated commit error"):
            await repo.persist_leads_batch(job.id, task_id=1, leads=[lead])

        mock_rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_idempotent_source_upsert(async_session: AsyncSession):
    """
    Regression Test 4:
    Verifies idempotent behavior: re-discovering a business updates last_seen_at
    without creating duplicate BusinessSource rows or overwriting created_at.
    """
    repo = DiscoveryRepository(async_session)
    job = DiscoveryJob(status=JobStatus.RUNNING, query={"target_audience": "Dentist"})
    async_session.add(job)
    await async_session.commit()
    await async_session.refresh(job)

    lead = DiscoveredLead(
        name="Idempotent Care",
        category="Dentist",
        city="Pune",
        phone="+919855555555",
        source_platform="google_maps",
        source_place_id="place_idem_1",
    )

    # First run: inserts new business & source
    new_c1, dup_c1 = await repo.persist_leads_batch(job.id, task_id=1, leads=[lead])
    assert new_c1 == 1
    assert dup_c1 == 0

    res = await async_session.execute(select(BusinessSource).where(BusinessSource.external_id == "place_idem_1"))
    src = res.scalars().one()
    initial_created_at = src.created_at
    initial_last_seen_at = src.last_seen_at

    # Second run: re-discovering same lead
    new_c2, dup_c2 = await repo.persist_leads_batch(job.id, task_id=1, leads=[lead])
    assert new_c2 == 0
    assert dup_c2 == 1

    await async_session.refresh(src)
    assert src.created_at == initial_created_at
    assert src.last_seen_at >= initial_last_seen_at

    # Total rows must still be exactly 1
    all_sources = (await async_session.execute(select(BusinessSource))).scalars().all()
    assert len(all_sources) == 1
