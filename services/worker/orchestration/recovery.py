"""
FastUI Task & Result Recovery Service
=====================================
Autonomous background service that periodically reclaims abandoned or stalled
messages across discovery tasks, discovery results, and enrichment streams.
Coordinates with PostgreSQL state to ensure zero lost leads or tasks.
"""

import asyncio
import json
import logging
from typing import Optional

from contracts.discovery import DiscoveredLead, DiscoveryResultMessage
from contracts.enrichment import EnrichmentTaskMessage
from core.constants import (
    GROUP_DISCOVERY_WORKERS,
    GROUP_ENRICHMENT_WORKERS,
    GROUP_RESULT_PROCESSORS,
    STREAM_DISCOVERY_RESULTS,
    STREAM_DISCOVERY_TASKS,
    STREAM_ENRICHMENT_TASKS,
)
from infrastructure.redis.streams import RedisStreams
from orchestration.enrichment import EnrichmentConsumer
from orchestration.results import ResultProcessor
from persistence.db import get_db_session
from persistence.models import TaskStatus
from persistence.repositories.discovery import DiscoveryRepository

logger = logging.getLogger("fastui.orchestration.recovery")


class TaskRecoveryService:
    """Monitors streams and reconciles stalled tasks with database state."""

    def __init__(
        self,
        streams: Optional[RedisStreams] = None,
        result_processor: Optional[ResultProcessor] = None,
        enrichment_consumer: Optional[EnrichmentConsumer] = None,
        consumer_name: str = "worker-recovery-1",
        poll_interval_sec: float = 60.0,
    ) -> None:
        self.streams = streams or RedisStreams()
        self.consumer_name = consumer_name
        self.poll_interval_sec = poll_interval_sec
        self.running = False
        self._result_processor = result_processor or ResultProcessor(
            streams=self.streams, consumer_name=self.consumer_name
        )
        self._enrichment_consumer = enrichment_consumer or EnrichmentConsumer(
            streams=self.streams, consumer_name=self.consumer_name
        )

    async def run(self) -> None:
        """Periodic reclamation loop."""
        self.running = True
        logger.info(
            f"TaskRecoveryService '{self.consumer_name}' started "
            f"(interval={self.poll_interval_sec}s)."
        )

        while self.running:
            try:
                await self.recover_all_streams()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task recovery cycle: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.poll_interval_sec)
            except asyncio.CancelledError:
                break

        logger.info(f"TaskRecoveryService '{self.consumer_name}' stopped.")

    async def recover_all_streams(self) -> None:
        """Executes recovery across discovery tasks, discovery results, and enrichment."""
        await self._recover_discovery_tasks()
        await self._recover_discovery_results()
        await self._recover_enrichment_tasks()

    async def _recover_discovery_tasks(self) -> None:
        """Reclaims discovery tasks idle for > 5 minutes and safely re-enqueues them."""
        claimed = await self.streams.autoclaim_abandoned(
            stream=STREAM_DISCOVERY_TASKS,
            group=GROUP_DISCOVERY_WORKERS,
            consumer_name=self.consumer_name,
            min_idle_time_ms=300000,  # 5 minutes
            count=10,
        )
        if not claimed:
            return

        logger.info(f"Recovered {len(claimed)} stalled discovery tasks.")
        for item in claimed:
            msg_id = item["id"]
            data = item["data"]
            task_id = int(data.get("task_id", 0))

            if not task_id:
                await self.streams.ack_discovery_task(msg_id)
                continue

            async with get_db_session() as session:
                repo = DiscoveryRepository(session)
                db_task = await repo.get_task(task_id)
                if not db_task:
                    await self.streams.ack_discovery_task(msg_id)
                    continue

                attempts = getattr(db_task, "attempts", 0)
                attempts_int = attempts if isinstance(attempts, int) else 0

                if db_task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.DEAD_LETTER):
                    # Task already terminal in DB; acknowledge message
                    await self.streams.ack_discovery_task(msg_id)
                elif attempts_int >= 3:
                    # Exceeded retry attempts; mark dead letter and acknowledge
                    logger.warning(f"Task {task_id} exceeded max retries ({attempts_int}); moving to DEAD_LETTER.")
                    await repo.update_task_status(task_id, TaskStatus.DEAD_LETTER, error_message="Exceeded max recovery attempts")
                    await self.streams.ack_discovery_task(msg_id)
                else:
                    # Reset to RETRYING, re-publish with fresh delivery, and ACK the stale message
                    logger.warning(f"Re-queuing stalled task {task_id} (attempt {attempts_int}).")
                    await repo.update_task_status(task_id, TaskStatus.RETRYING)
                    await self.streams.publish_discovery_task(
                        task_id=db_task.id,
                        job_id=db_task.job_id,
                        params=db_task.params,
                    )
                    await self.streams.ack_discovery_task(msg_id)

    async def _recover_discovery_results(self) -> None:
        """Reclaims discovery results idle for > 2 minutes and re-processes them."""
        claimed = await self.streams.autoclaim_abandoned(
            stream=STREAM_DISCOVERY_RESULTS,
            group=GROUP_RESULT_PROCESSORS,
            consumer_name=self.consumer_name,
            min_idle_time_ms=600000,  # 10 minutes — prevents re-claiming batches still processing
            count=10,
        )
        if not claimed:
            return

        logger.info(f"Recovered and processing {len(claimed)} stalled discovery result messages.")
        for item in claimed:
            msg_id = item["id"]
            data = item["data"]
            try:
                job_id = int(data.get("job_id", 0))
                task_id = int(data.get("task_id", 0))
                leads_raw = data.get("leads", "[]")
                leads_list = json.loads(leads_raw) if isinstance(leads_raw, str) else leads_raw
                leads = [DiscoveredLead.model_validate(item) for item in leads_list]

                exhausted = data.get("exhausted") in ("1", "true", "True", True)
                next_cursor = data.get("next_cursor") or None
                current_locality = data.get("current_locality") or None
                loc_rem = data.get("localities_remaining")
                localities_remaining = int(loc_rem) if loc_rem and str(loc_rem).strip() else None

                res_msg = DiscoveryResultMessage(
                    message_id=msg_id,
                    job_id=job_id,
                    task_id=task_id,
                    leads=leads,
                    exhausted=exhausted,
                    next_cursor=next_cursor,
                    current_locality=current_locality,
                    localities_remaining=localities_remaining,
                    error=data.get("error") or None,
                )
                await self._result_processor.process_result(res_msg)
            except Exception as e:
                logger.error(f"Failed to process recovered result {msg_id}: {e}", exc_info=True)
                await self.streams.ack_discovery_result(msg_id)

    async def _recover_enrichment_tasks(self) -> None:
        """Reclaims enrichment tasks idle for > 3 minutes and processes them."""
        claimed = await self.streams.autoclaim_abandoned(
            stream=STREAM_ENRICHMENT_TASKS,
            group=GROUP_ENRICHMENT_WORKERS,
            consumer_name=self.consumer_name,
            min_idle_time_ms=180000,  # 3 minutes
            count=10,
        )
        if not claimed:
            return

        logger.info(f"Recovered and processing {len(claimed)} stalled enrichment tasks.")
        for item in claimed:
            msg_id = item["id"]
            data = item["data"]
            try:
                task_msg = EnrichmentTaskMessage(
                    message_id=msg_id,
                    business_id=int(data.get("business_id", 0)),
                    website=data.get("website", ""),
                    business_name=data.get("business_name") or None,
                    max_pages=int(data.get("max_pages", 4)),
                )
                await self._enrichment_consumer.process_task(task_msg)
            except Exception as e:
                logger.error(f"Failed to process recovered enrichment task {msg_id}: {e}", exc_info=True)
                await self.streams.ack_enrichment_task(msg_id)

    async def stop(self) -> None:
        """Signals the recovery service to stop."""
        self.running = False
