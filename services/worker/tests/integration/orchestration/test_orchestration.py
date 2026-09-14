"""
Integration tests for orchestration consumers and task recovery service.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from contracts.discovery import DiscoveredLead, DiscoveryResultMessage
from contracts.enrichment import (
    EnrichedBusinessProfile,
    EnrichmentResponse,
    EnrichmentTaskMessage,
)
from orchestration.enrichment import EnrichmentConsumer
from orchestration.recovery import TaskRecoveryService
from orchestration.results import ResultProcessor
from persistence.models import TaskStatus


@pytest.mark.asyncio
async def test_result_processor_flow():
    mock_streams = MagicMock()
    mock_streams.claim_discovery_results = AsyncMock(
        side_effect=[
            [
                DiscoveryResultMessage(
                    message_id="msg_123",
                    job_id=1,
                    task_id=10,
                    leads=[
                        DiscoveredLead(
                            name="Apex Dental",
                            city="Ahmedabad",
                            website="https://apexdental.com",
                            source_platform="google_maps",
                        )
                    ],
                    exhausted=True,
                )
            ],
            [],
        ]
    )
    mock_streams.ack_discovery_result = AsyncMock()
    mock_streams.publish_enrichment_task = AsyncMock()

    processor = ResultProcessor(streams=mock_streams)

    with patch("orchestration.results.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("orchestration.results.DiscoveryRepository") as MockRepo:
            mock_repo_instance = AsyncMock()
            # persist_leads_batch now returns (new_count, dup_count) — no enrichment_targets
            mock_repo_instance.persist_leads_batch.return_value = (1, 0)
            MockRepo.return_value = mock_repo_instance

            # Process 1 batch
            results = await mock_streams.claim_discovery_results()
            for res in results:
                await processor.process_result(res)

            assert mock_repo_instance.persist_leads_batch.call_count == 1
            assert mock_repo_instance.update_job_progress.call_count == 1
            assert mock_streams.ack_discovery_result.call_count == 1
            # Discovery must never trigger enrichment as a side effect
            mock_streams.publish_enrichment_task.assert_not_called()


@pytest.mark.asyncio
async def test_discovery_pipeline_end_to_end_isolation_from_enrichment():
    """
    Architectural Invariant Test:
    Proves that the entire discovery pipeline (DiscoveryConsumer + ResultProcessor)
    processes leads with websites, deduplicates, persists, and updates progress,
    with ZERO enrichment tasks enqueued or enrichment code executed.
    """
    from contracts.discovery import DiscoveryTaskMessage
    from orchestration.discovery import DiscoveryConsumer

    mock_streams = MagicMock()
    mock_streams.publish_discovery_result = AsyncMock()
    mock_streams.publish_discovery_task = AsyncMock()
    mock_streams.ack_discovery_task = AsyncMock()
    mock_streams.ack_discovery_result = AsyncMock()
    mock_streams.publish_enrichment_task = AsyncMock()

    # 1. Test DiscoveryConsumer with 5 leads having websites
    consumer = DiscoveryConsumer(streams=mock_streams)
    task_msg = DiscoveryTaskMessage(
        message_id="task_msg_1",
        task_id=50,
        job_id=5,
    )

    scraped_leads = [
        DiscoveredLead(
            name=f"Clinic {i}",
            city="Delhi",
            website=f"https://clinic{i}.example.com",
            phone=f"+91981100000{i}",
            source_platform="google_maps",
        )
        for i in range(1, 6)
    ]

    with patch("orchestration.discovery.get_db_session") as mock_db, patch(
        "orchestration.discovery.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_thread:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("orchestration.discovery.DiscoveryRepository") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_task = MagicMock()
            mock_task.id = 50
            mock_task.job_id = 5
            mock_task.params = {"target_audience": "Dentist", "location": "Delhi"}
            mock_repo_instance.get_task.return_value = mock_task
            MockRepo.return_value = mock_repo_instance

            # Thread scraper returns scraped leads, exhausted=True, no cursor
            mock_thread.return_value = (scraped_leads, True, {}, 50.0, None, None, None)

            await consumer.process_task(task_msg)

            # Discovery result published
            mock_streams.publish_discovery_result.assert_called_once()
            # Task marked running then succeeded
            mock_repo_instance.update_task_status.assert_called_with(50, TaskStatus.SUCCEEDED)
            # Discovery stream acknowledged
            mock_streams.ack_discovery_task.assert_called_once_with("task_msg_1")
            # ENRICHMENT WAS NEVER TOUCHED
            mock_streams.publish_enrichment_task.assert_not_called()

    # 2. Test ResultProcessor persisting those 5 leads
    processor = ResultProcessor(streams=mock_streams)
    result_msg = DiscoveryResultMessage(
        message_id="res_msg_5",
        job_id=5,
        task_id=50,
        leads=scraped_leads,
        exhausted=True,
    )

    with patch("orchestration.results.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("orchestration.results.DiscoveryRepository") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.persist_leads_batch.return_value = (5, 0)
            MockRepo.return_value = mock_repo_instance

            await processor.process_result(result_msg)

            mock_repo_instance.persist_leads_batch.assert_called_once_with(5, 50, scraped_leads)
            mock_repo_instance.update_job_progress.assert_called_once_with(
                job_id=5, new_leads=5, duplicates=0, is_exhausted=True
            )
            mock_streams.ack_discovery_result.assert_called_once_with("res_msg_5")
            # ENRICHMENT WAS NEVER TOUCHED
            mock_streams.publish_enrichment_task.assert_not_called()



@pytest.mark.asyncio
async def test_enrichment_consumer_flow():
    mock_streams = MagicMock()
    mock_streams.claim_enrichment_tasks = AsyncMock()
    mock_streams.ack_enrichment_task = AsyncMock()

    consumer = EnrichmentConsumer(streams=mock_streams)

    task_msg = EnrichmentTaskMessage(
        message_id="enrich_msg_1",
        business_id=42,
        website="https://apexdental.com",
        business_name="Apex Dental",
        max_pages=2,
    )

    mock_resp = EnrichmentResponse(
        success=True,
        status="completed",
        profile=EnrichedBusinessProfile(website_url="https://apexdental.com"),
    )

    with patch.object(consumer.engine, "enrich_website", new_callable=AsyncMock) as mock_enrich:
        mock_enrich.return_value = mock_resp

        with patch("orchestration.enrichment.get_db_session") as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            with patch("orchestration.enrichment.EnrichmentRepository") as MockRepo:
                mock_repo_instance = AsyncMock()
                MockRepo.return_value = mock_repo_instance

                await consumer.process_task(task_msg)

                assert mock_repo_instance.save_enrichment_result.call_count == 1
                assert mock_streams.ack_enrichment_task.call_count == 1


@pytest.mark.asyncio
async def test_task_recovery_service_cycle():
    mock_streams = MagicMock()
    mock_streams.autoclaim_abandoned = AsyncMock(
        side_effect=[
            [{"id": "stalled_task_1", "data": {"task_id": "100", "job_id": "1"}}],
            [],  # results
            [],  # enrichment
        ]
    )
    mock_streams.ack_discovery_task = AsyncMock()
    mock_streams.publish_discovery_task = AsyncMock()

    service = TaskRecoveryService(streams=mock_streams)

    with patch("orchestration.recovery.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("orchestration.recovery.DiscoveryRepository") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_task = MagicMock()
            mock_task.id = 100
            mock_task.job_id = 1
            mock_task.params = {}
            mock_task.status = "running"
            mock_task.attempts = 1
            mock_repo_instance.get_task.return_value = mock_task
            MockRepo.return_value = mock_repo_instance

            await service.recover_all_streams()

            assert mock_streams.autoclaim_abandoned.call_count == 3
            assert mock_repo_instance.update_task_status.call_count == 1
            assert mock_streams.publish_discovery_task.call_count == 1
            assert mock_streams.ack_discovery_task.call_count == 1
