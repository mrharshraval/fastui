"""
FastUI Enrichment Task Consumer
===============================
Consumes website enrichment tasks from Redis streams, orchestrates multi-page
crawling, and saves extracted prospect profiles via EnrichmentRepository.
"""

import asyncio
import logging
from typing import Optional, Set

from core.config import settings

from contracts.enrichment import EnrichmentParams, EnrichmentTaskMessage
from enrichment.engine import WebsiteEnrichmentEngine
from infrastructure.redis.streams import RedisStreams
from persistence.db import get_db_session
from persistence.repositories.enrichment import EnrichmentRepository

logger = logging.getLogger("fastui.orchestration.enrichment")


class EnrichmentConsumer:
    """Manages claiming, concurrency control, and execution of website enrichment tasks."""

    def __init__(
        self,
        streams: Optional[RedisStreams] = None,
        engine: Optional[WebsiteEnrichmentEngine] = None,
        consumer_name: str = "worker-enrichment-1",
        max_concurrency: Optional[int] = None,
    ) -> None:
        self.streams = streams or RedisStreams()
        self.consumer_name = consumer_name
        self.semaphore = asyncio.Semaphore(max_concurrency or settings.MAX_CONCURRENT_ENRICHMENT)
        self.engine = engine or WebsiteEnrichmentEngine()
        self.running = False
        self._running_tasks: Set[asyncio.Task] = set()

    async def run(self) -> None:
        """Continuous enrichment consumption loop."""
        self.running = True
        logger.info(f"EnrichmentConsumer '{self.consumer_name}' started.")

        while self.running:
            try:
                tasks = await self.streams.claim_enrichment_tasks(
                    consumer_name=self.consumer_name,
                    count=1,
                    block_ms=2000,
                )
                for task_msg in tasks:
                    await self.semaphore.acquire()
                    bg_task = asyncio.create_task(
                        self._process_task_wrapper(task_msg),
                        name=f"EnrichmentTask-{task_msg.business_id}",
                    )
                    self._running_tasks.add(bg_task)
                    bg_task.add_done_callback(self._running_tasks.discard)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in enrichment consumer loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info(f"EnrichmentConsumer '{self.consumer_name}' stopped.")

    async def _process_task_wrapper(self, task_msg: EnrichmentTaskMessage) -> None:
        try:
            await self.process_task(task_msg)
        finally:
            self.semaphore.release()

    async def process_task(self, task_msg: EnrichmentTaskMessage) -> None:
        """Executes enrichment analysis for a single business website."""
        business_id = task_msg.business_id
        website = task_msg.website
        logger.info(f"Enriching website '{website}' for business {business_id}...")

        params = EnrichmentParams(
            website=website,
            business_name=task_msg.business_name,
            max_pages=task_msg.max_pages,
        )

        try:
            resp = await self.engine.enrich_website(params)
            async with get_db_session() as session:
                repo = EnrichmentRepository(session)
                if resp.success and resp.profile:
                    await repo.save_enrichment_result(business_id, resp.profile)
                    logger.info(f"Successfully saved enriched profile for business {business_id}.")
                else:
                    await repo.record_enrichment_failure(business_id, resp.error or "Unknown failure")

            await self.streams.ack_enrichment_task(task_msg.message_id)

        except Exception as e:
            logger.error(f"Enrichment failed for business {business_id} ({website}): {e}", exc_info=True)
            async with get_db_session() as session:
                repo = EnrichmentRepository(session)
                await repo.record_enrichment_failure(business_id, str(e))
            await self.streams.ack_enrichment_task(task_msg.message_id)

    async def stop(self) -> None:
        """Signals the consumer loop to stop."""
        self.running = False

    async def drain(self, timeout_sec: float = 30.0) -> None:
        """Waits for all active enrichment tasks to conclude and closes client connections."""
        if self._running_tasks:
            logger.info(f"Draining {len(self._running_tasks)} active enrichment tasks...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._running_tasks, return_exceptions=True),
                    timeout=timeout_sec,
                )
            except asyncio.TimeoutError:
                logger.warning("Enrichment task draining timed out; canceling active tasks.")
                for t in self._running_tasks:
                    t.cancel()

        # Deterministically close pooled HTTP connections
        await self.engine.client.aclose()

    _process_single_task = process_task

