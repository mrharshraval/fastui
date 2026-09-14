"""
FastUI Discovery Task Consumer
==============================
Consumes discovery tasks from Redis streams, orchestrates multi-source scraping
under bounded concurrency, and publishes discovered leads to the results stream.
"""

import asyncio
import logging
import sys
from typing import Optional, Set

from contracts.discovery import DiscoverySearchParams, DiscoveryTaskMessage
from core.config import settings
from core.constants import STREAM_DISCOVERY_RESULTS
from infrastructure.redis.streams import RedisStreams
from persistence.db import get_db_session
from persistence.models import TaskStatus
from persistence.repositories.discovery import DiscoveryRepository
from sources.aggregator import MultiSourceDiscoveryAggregator

logger = logging.getLogger("fastui.orchestration.discovery")


def _run_discovery_in_proactor(params: DiscoverySearchParams, headless: bool):
    """Runs Playwright scraping in an isolated runner with appropriate event loop."""
    loop_factory = asyncio.ProactorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        aggregator = MultiSourceDiscoveryAggregator(headless=headless)
        return runner.run(aggregator.discover_with_meta(params))


class DiscoveryConsumer:
    """Manages claiming, concurrency-limiting, and execution of lead discovery tasks."""

    def __init__(
        self,
        streams: Optional[RedisStreams] = None,
        consumer_name: str = "worker-discovery-1",
    ) -> None:
        self.streams = streams or RedisStreams()
        self.consumer_name = consumer_name
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_SCRAPERS)
        self.running = False
        self._running_tasks: Set[asyncio.Task] = set()

    async def run(self) -> None:
        """Continuous task consumption loop."""
        self.running = True
        logger.info(
            f"DiscoveryConsumer '{self.consumer_name}' started "
            f"(max_concurrency={settings.MAX_CONCURRENT_SCRAPERS})."
        )

        while self.running:
            try:
                # Backpressure protection: check if results stream backlog is high
                results_depth = await self.streams.get_stream_depth(STREAM_DISCOVERY_RESULTS)
                if results_depth >= settings.BACKPRESSURE_MAX_PENDING_RESULTS:
                    logger.warning(
                        f"Backpressure applied: '{STREAM_DISCOVERY_RESULTS}' backlog depth {results_depth} >= "
                        f"threshold {settings.BACKPRESSURE_MAX_PENDING_RESULTS}. Pausing discovery claiming..."
                    )
                    await asyncio.sleep(2.0)
                    continue

                tasks = await self.streams.claim_discovery_tasks(
                    consumer_name=self.consumer_name,
                    count=1,
                    block_ms=2000,
                )
                for task_msg in tasks:
                    await self.semaphore.acquire()
                    bg_task = asyncio.create_task(
                        self._process_task_wrapper(task_msg),
                        name=f"DiscoveryTask-{task_msg.task_id}",
                    )
                    self._running_tasks.add(bg_task)
                    bg_task.add_done_callback(self._running_tasks.discard)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery consumer loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info(f"DiscoveryConsumer '{self.consumer_name}' stopped.")

    async def _process_task_wrapper(self, task_msg: DiscoveryTaskMessage) -> None:
        try:
            await self.process_task(task_msg)
        finally:
            self.semaphore.release()

    async def process_task(self, task_msg: DiscoveryTaskMessage) -> None:
        """Executes a single discovery task and publishes results."""
        task_id = task_msg.task_id
        job_id = task_msg.job_id
        logger.info(f"Processing discovery task {task_id} for job {job_id}...")

        # 1. Update task status in DB
        async with get_db_session() as session:
            repo = DiscoveryRepository(session)
            db_task = await repo.get_task(task_id)
            if not db_task:
                logger.warning(f"Task {task_id} not found in database; acknowledging.")
                await self.streams.ack_discovery_task(task_msg.message_id)
                return

            await repo.update_task_status(task_id, TaskStatus.RUNNING)
            params_dict = db_task.params or {}

        # 2. Parse search parameters
        params = DiscoverySearchParams.model_validate(params_dict)

        # 3. Execute scraping pipeline in dedicated thread
        try:
            (
                leads,
                exhausted,
                _sources_exhausted,
                _peak_rss,
                next_cursor,
                current_locality,
                localities_remaining,
            ) = await asyncio.to_thread(
                _run_discovery_in_proactor,
                params,
                settings.HEADLESS_BROWSER,
            )

            # 4. Publish leads to fastui:discover:results
            await self.streams.publish_discovery_result(
                job_id=job_id,
                task_id=task_id,
                leads=leads,
                exhausted=exhausted,
                next_cursor=next_cursor,
                current_locality=current_locality,
                localities_remaining=localities_remaining,
            )

            # 5. Handle pagination/continuation tasks
            if next_cursor and not exhausted:
                continuation_params = dict(params_dict)
                continuation_params["cursor"] = next_cursor
                continuation_params["locality"] = current_locality

                async with get_db_session() as session:
                    repo = DiscoveryRepository(session)
                    cont_task = await repo.create_continuation_task(job_id, continuation_params)

                # Dispatch continuation task to Redis stream
                await self.streams.publish_discovery_task(
                    task_id=cont_task.id,
                    job_id=job_id,
                    params=continuation_params,
                )
                logger.info(f"Scheduled continuation task {cont_task.id} for job {job_id}.")

            # 6. Mark task succeeded in DB and ACK message
            async with get_db_session() as session:
                repo = DiscoveryRepository(session)
                await repo.update_task_status(task_id, TaskStatus.SUCCEEDED)

            await self.streams.ack_discovery_task(task_msg.message_id)
            logger.info(f"Discovery task {task_id} succeeded with {len(leads)} leads.")

        except Exception as e:
            logger.error(f"Discovery task {task_id} execution failed: {e}", exc_info=True)
            async with get_db_session() as session:
                repo = DiscoveryRepository(session)
                await repo.update_task_status(task_id, TaskStatus.FAILED, error_message=str(e))
            await self.streams.ack_discovery_task(task_msg.message_id)

    async def stop(self) -> None:
        """Signals the consumer loop to stop."""
        self.running = False

    async def drain(self, timeout_sec: float = 30.0) -> None:
        """Waits for currently running scraping tasks to conclude before process exit."""
        if not self._running_tasks:
            return
        logger.info(f"Draining {len(self._running_tasks)} running discovery tasks...")
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._running_tasks, return_exceptions=True),
                timeout=timeout_sec,
            )
        except asyncio.TimeoutError:
            logger.warning("Discovery task draining timed out; canceling active tasks.")
            for t in self._running_tasks:
                t.cancel()
