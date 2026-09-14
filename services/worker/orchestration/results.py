"""
FastUI Discovery Result Processor
=================================
Consumes scraped lead batches from Redis streams and coordinates deduplicated
persistence via DiscoveryRepository.

Enrichment is an independent, explicitly triggered workflow. This processor
never enqueues enrichment tasks as a side effect of discovery.
"""

import asyncio
import logging
from typing import Optional

from contracts.discovery import DiscoveryResultMessage
from infrastructure.redis.streams import RedisStreams
from persistence.db import get_db_session
from persistence.repositories.discovery import DiscoveryRepository

logger = logging.getLogger("fastui.orchestration.results")


class ResultProcessor:
    """Consumes and persists discovery results with transactional deduplication."""

    def __init__(
        self,
        streams: Optional[RedisStreams] = None,
        consumer_name: str = "worker-results-1",
    ) -> None:
        self.streams = streams or RedisStreams()
        self.consumer_name = consumer_name
        self.running = False

    async def run(self) -> None:
        """Continuous results processing loop."""
        self.running = True
        logger.info(f"ResultProcessor '{self.consumer_name}' started.")

        while self.running:
            try:
                results = await self.streams.claim_discovery_results(
                    consumer_name=self.consumer_name,
                    count=1,
                    block_ms=2000,
                )
                for res_msg in results:
                    await self.process_result(res_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in result processor loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info(f"ResultProcessor '{self.consumer_name}' stopped.")

    async def process_result(self, res_msg: DiscoveryResultMessage) -> None:
        """Persists a batch of discovered leads and updates job progress."""
        job_id = res_msg.job_id
        task_id = res_msg.task_id
        leads = res_msg.leads

        logger.info(
            f"Processing {len(leads)} leads for job {job_id}, task {task_id} "
            f"(msg_id={res_msg.message_id})..."
        )

        async with get_db_session() as session:
            repo = DiscoveryRepository(session)

            # 1. Deduplicated batch persistence
            new_count, dup_count = await repo.persist_leads_batch(
                job_id, task_id, leads
            )

            # 2. Update job aggregate counters and completion
            await repo.update_job_progress(
                job_id=job_id,
                new_leads=new_count,
                duplicates=dup_count,
                is_exhausted=res_msg.exhausted,
            )

        # 3. Acknowledge stream message
        await self.streams.ack_discovery_result(res_msg.message_id)
        logger.info(
            f"Result message {res_msg.message_id} committed: {new_count} new, {dup_count} duplicates."
        )

    async def stop(self) -> None:
        """Signals the processor loop to stop."""
        self.running = False
