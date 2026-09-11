"""
Tests for Google Maps location verification, canonical place URL retrieval,
and locality cursor progression in DiscoveryService and BusinessService.
"""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.service import BusinessService
from app.domains.models import Business, BusinessSource, DiscoveryJob, JobStatus
from app.domains.prospecting.service import ProspectingService as DiscoveryService
from app.domains.prospects.service import ProspectsService
from app.infrastructure.external.worker_client import (
    WorkerDiscoveredLead as DiscoveredLead,
)
from app.infrastructure.external.worker_client import (
    WorkerDiscoverResponse as DiscoverResponse,
)


@pytest.mark.asyncio
async def test_business_service_returns_verified_location_metadata(
    db_session: AsyncSession,
):
    """
    Verifies that BusinessService.get_business_by_id and get_prospects return
    google_maps_url, latitude, longitude, and google_place_id populated from BusinessSource.
    """
    # 1. Create a business
    biz = Business(
        business_name="Apex Dental Care",
        category="Dentist",
        city="Ahmedabad",
        qualification_status="unqualified",
        address="Navrangpura, Ahmedabad",
    )
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    # 2. Add Google Maps source with verified canonical URL and pin coordinates
    maps_source = BusinessSource(
        business_id=biz.id,
        platform="google_maps",
        source_url="https://www.google.com/maps?cid=5746960032305554312",
        external_id="0x395e848aba5bd449:0x4fc14db35ff0a388",
        raw_payload={
            "latitude": 23.033812,
            "longitude": 72.585034,
            "place_id": "0x395e848aba5bd449:0x4fc14db35ff0a388",
            "google_maps_url": "https://www.google.com/maps?cid=5746960032305554312",
        },
    )
    db_session.add(maps_source)
    await db_session.commit()

    # 3. Test get_business_by_id
    detail = await BusinessService.get_business_by_id(db_session, biz.id)
    assert detail.google_maps_url == "https://www.google.com/maps?cid=5746960032305554312"
    assert detail.latitude == 23.033812
    assert detail.longitude == 72.585034
    assert detail.google_place_id == "0x395e848aba5bd449:0x4fc14db35ff0a388"

    # 4. Test get_prospects batch retrieval
    prospects = await ProspectsService.list_prospects(db_session, limit=10)
    prospect = next((p for p in prospects if p.id == biz.id), None)
    assert prospect is not None
    assert prospect.google_maps_url == "https://www.google.com/maps?cid=5746960032305554312"
    assert prospect.latitude == 23.033812
    assert prospect.longitude == 72.585034


@pytest.mark.asyncio
async def test_discovery_service_locality_cursor_progression(
    db_session: AsyncSession,
):
    """
    Verifies that DiscoveryService progresses across locality cursors (e.g. loc:0 -> loc:1)
    and does not terminate prematurely even when duplicates occur if localities_remaining > 0.
    """
    job = DiscoveryJob(
        query={
            "business_type": "Dentist",
            "location": {"city": "Ahmedabad"},
            "target_count": 2,
        },
        status=JobStatus.QUEUED,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Lead 1 from Locality 0 (Navrangpura)
    lead1 = DiscoveredLead(
        name="Navrang Dental",
        category="Dentist",
        city="Ahmedabad",
        phone="+917926401111",
        google_maps_url="https://www.google.com/maps?cid=1111111111111111111",
        google_place_id="0x395e840000000001:0x1111111111111111",
        latitude=23.035,
        longitude=72.560,
        source_platform="google_maps",
    )

    # Lead 2 from Locality 1 (Bodakdev)
    lead2 = DiscoveredLead(
        name="Bodakdev Dental Clinic",
        category="Dentist",
        city="Ahmedabad",
        phone="+917926402222",
        google_maps_url="https://www.google.com/maps?cid=2222222222222222222",
        google_place_id="0x395e840000000002:0x2222222222222222",
        latitude=23.045,
        longitude=72.510,
        source_platform="google_maps",
    )

    batch_responses = [
        DiscoverResponse(
            leads=[lead1],
            count=1,
            next_cursor="loc:1",
            current_locality="Navrangpura",
            localities_remaining=10,
        ),
        DiscoverResponse(
            leads=[lead2],
            count=1,
            next_cursor=None,
            current_locality="Bodakdev",
            localities_remaining=0,
        ),
    ]

    worker_calls = []

    async def mock_discover_batch(search_params):
        worker_calls.append(search_params.model_dump())
        return batch_responses.pop(0)

    with patch(
        "app.domains.prospecting.service.WorkerClient.discover_batch",
        side_effect=mock_discover_batch,
    ):
        await DiscoveryService.process_job(job.id)

    await db_session.refresh(job)
    assert job.status == JobStatus.COMPLETED
    assert job.new_leads == 2
    assert len(worker_calls) == 2

    # Check that the second call received the advanced cursor
    assert worker_calls[0].get("cursor") is None
    assert worker_calls[1].get("cursor") == "loc:1"
