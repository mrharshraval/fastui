"""
FastUI Redis Streams Infrastructure
===================================
Typed stream message operations, consumer group initialization, and message claiming.
Isolates all raw Redis commands (XADD, XREADGROUP, XACK, XAUTOCLAIM).
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    ResponseError,
    TimeoutError as RedisTimeoutError,
)

from contracts.discovery import (
    DiscoveredLead,
    DiscoveryResultMessage,
    DiscoverySearchParams,
    DiscoveryTaskMessage,
)
from contracts.enrichment import EnrichmentTaskMessage
from core.config import settings
from core.constants import (
    GROUP_DISCOVERY_WORKERS,
    GROUP_ENRICHMENT_WORKERS,
    GROUP_RESULT_PROCESSORS,
    STREAM_DISCOVERY_RESULTS,
    STREAM_DISCOVERY_TASKS,
    STREAM_ENRICHMENT_TASKS,
)
from infrastructure.redis.client import get_redis_client

logger = logging.getLogger("fastui.infra.streams")


class RedisStreams:
    """Encapsulates Redis Streams message transport and group management."""

    def __init__(self, client: Optional[redis.Redis] = None) -> None:
        self._client = client

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    async def ensure_groups(self) -> None:
        """Initializes all consumer groups and streams if they do not exist."""
        groups = [
            (STREAM_DISCOVERY_TASKS, GROUP_DISCOVERY_WORKERS),
            (STREAM_DISCOVERY_RESULTS, GROUP_RESULT_PROCESSORS),
            (STREAM_ENRICHMENT_TASKS, GROUP_ENRICHMENT_WORKERS),
        ]
        for stream, group in groups:
            try:
                await self.client.xgroup_create(stream, group, id="0", mkstream=True)
                logger.info(f"Initialized consumer group '{group}' on stream '{stream}'.")
            except ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.error(f"Failed to create group '{group}' on '{stream}': {e}")
                    raise

    # ─────────────────────────────────────────────────────────────
    # DISCOVERY TASKS (fastui:discover:tasks)
    # ─────────────────────────────────────────────────────────────

    async def publish_discovery_task(
        self,
        task_id: int,
        job_id: int,
        params: Optional[Any] = None,
    ) -> str:
        """Publishes a new or continuation discovery task to fastui:discover:tasks."""
        payload: Dict[str, str] = {
            "task_id": str(task_id),
            "job_id": str(job_id),
        }
        if params is not None:
            if hasattr(params, "model_dump"):
                payload["params"] = json.dumps(params.model_dump())
            elif isinstance(params, (dict, list)):
                payload["params"] = json.dumps(params)
            else:
                payload["params"] = str(params)

        return await self.client.xadd(
            STREAM_DISCOVERY_TASKS,
            payload,
            maxlen=settings.REDIS_STREAM_MAXLEN,
            approximate=True,
        )

    async def claim_discovery_tasks(
        self,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 2000,
    ) -> List[DiscoveryTaskMessage]:
        """Reads new discovery tasks for the given consumer."""
        try:
            response = await self.client.xreadgroup(
                groupname=GROUP_DISCOVERY_WORKERS,
                consumername=consumer_name,
                streams={STREAM_DISCOVERY_TASKS: ">"},
                count=count,
                block=block_ms,
            )
            if not response:
                return []

            messages: List[DiscoveryTaskMessage] = []
            for _stream_name, stream_messages in response:
                for msg_id, data in stream_messages:
                    try:
                        task_id = int(data.get("task_id", 0))
                        job_id = int(data.get("job_id", 0))
                        params_raw = data.get("params")
                        params = None
                        if params_raw:
                            p_dict = json.loads(params_raw) if isinstance(params_raw, str) else params_raw
                            params = DiscoverySearchParams.model_validate(p_dict)
                        messages.append(
                            DiscoveryTaskMessage(
                                message_id=msg_id,
                                task_id=task_id,
                                job_id=job_id,
                                params=params,
                            )
                        )
                    except Exception as e:
                        logger.error(f"Failed to parse discovery task message {msg_id}: {e}")
            return messages
        except (RedisTimeoutError, RedisConnectionError) as e:
            logger.warning(f"Transient Redis timeout/disconnect on '{STREAM_DISCOVERY_TASKS}': {e}. Retrying...")
            return []
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error reading from '{STREAM_DISCOVERY_TASKS}': {e}", exc_info=True)
            return []

    async def ack_discovery_task(self, message_id: str) -> None:
        """Acknowledges a processed discovery task."""
        await self.client.xack(STREAM_DISCOVERY_TASKS, GROUP_DISCOVERY_WORKERS, message_id)

    # ─────────────────────────────────────────────────────────────
    # DISCOVERY RESULTS (fastui:discover:results)
    # ─────────────────────────────────────────────────────────────

    async def publish_discovery_result(
        self,
        job_id: int,
        task_id: int,
        leads: List[DiscoveredLead],
        exhausted: bool = False,
        next_cursor: Optional[str] = None,
        current_locality: Optional[str] = None,
        localities_remaining: Optional[int] = None,
        error: Optional[str] = None,
    ) -> str:
        """Publishes scraper results to fastui:discover:results."""
        leads_data = [lead.model_dump() for lead in leads]
        payload = {
            "job_id": str(job_id),
            "task_id": str(task_id),
            "leads": json.dumps(leads_data),
            "exhausted": "1" if exhausted else "0",
            "next_cursor": next_cursor or "",
            "current_locality": current_locality or "",
            "localities_remaining": str(localities_remaining) if localities_remaining is not None else "",
            "error": error or "",
        }
        msg_id = await self.client.xadd(
            STREAM_DISCOVERY_RESULTS,
            payload,
            maxlen=settings.REDIS_STREAM_MAXLEN,
            approximate=True,
        )
        logger.info(
            f"Published {len(leads)} leads for task {task_id}, job {job_id} to '{STREAM_DISCOVERY_RESULTS}' (msg_id={msg_id})."
        )
        return msg_id

    async def claim_discovery_results(
        self,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 2000,
    ) -> List[DiscoveryResultMessage]:
        """Reads scraper results from fastui:discover:results."""
        try:
            response = await self.client.xreadgroup(
                groupname=GROUP_RESULT_PROCESSORS,
                consumername=consumer_name,
                streams={STREAM_DISCOVERY_RESULTS: ">"},
                count=count,
                block=block_ms,
            )
            if not response:
                return []

            results: List[DiscoveryResultMessage] = []
            for _stream_name, stream_messages in response:
                for msg_id, data in stream_messages:
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
                        error = data.get("error") or None

                        results.append(
                            DiscoveryResultMessage(
                                message_id=msg_id,
                                job_id=job_id,
                                task_id=task_id,
                                leads=leads,
                                exhausted=exhausted,
                                next_cursor=next_cursor,
                                current_locality=current_locality,
                                localities_remaining=localities_remaining,
                                error=error,
                            )
                        )
                    except Exception as e:
                        logger.error(f"Failed to parse discovery result message {msg_id}: {e}")
            return results
        except (RedisTimeoutError, RedisConnectionError) as e:
            logger.warning(f"Transient Redis timeout/disconnect on '{STREAM_DISCOVERY_RESULTS}': {e}. Retrying...")
            return []
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error reading from '{STREAM_DISCOVERY_RESULTS}': {e}", exc_info=True)
            return []

    async def ack_discovery_result(self, message_id: str) -> None:
        """Acknowledges a processed discovery result."""
        await self.client.xack(STREAM_DISCOVERY_RESULTS, GROUP_RESULT_PROCESSORS, message_id)

    # ─────────────────────────────────────────────────────────────
    # ENRICHMENT TASKS (fastui:enrich:tasks)
    # ─────────────────────────────────────────────────────────────

    async def publish_enrichment_task(
        self,
        business_id: int,
        website: str,
        business_name: Optional[str] = None,
        max_pages: int = 4,
    ) -> str:
        """Publishes an enrichment task to fastui:enrich:tasks."""
        payload = {
            "business_id": str(business_id),
            "website": website,
            "business_name": business_name or "",
            "max_pages": str(max_pages),
        }
        return await self.client.xadd(
            STREAM_ENRICHMENT_TASKS,
            payload,
            maxlen=settings.REDIS_STREAM_MAXLEN,
            approximate=True,
        )

    async def claim_enrichment_tasks(
        self,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 2000,
    ) -> List[EnrichmentTaskMessage]:
        """Reads enrichment tasks from fastui:enrich:tasks."""
        try:
            response = await self.client.xreadgroup(
                groupname=GROUP_ENRICHMENT_WORKERS,
                consumername=consumer_name,
                streams={STREAM_ENRICHMENT_TASKS: ">"},
                count=count,
                block=block_ms,
            )
            if not response:
                return []

            tasks: List[EnrichmentTaskMessage] = []
            for _stream_name, stream_messages in response:
                for msg_id, data in stream_messages:
                    try:
                        tasks.append(
                            EnrichmentTaskMessage(
                                message_id=msg_id,
                                business_id=int(data.get("business_id", 0)),
                                website=data.get("website", ""),
                                business_name=data.get("business_name") or None,
                                max_pages=int(data.get("max_pages", 4)),
                            )
                        )
                    except Exception as e:
                        logger.error(f"Failed to parse enrichment task {msg_id}: {e}")
            return tasks
        except (RedisTimeoutError, RedisConnectionError) as e:
            logger.warning(f"Transient Redis timeout/disconnect on '{STREAM_ENRICHMENT_TASKS}': {e}. Retrying...")
            return []
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error reading from '{STREAM_ENRICHMENT_TASKS}': {e}", exc_info=True)
            return []

    async def ack_enrichment_task(self, message_id: str) -> None:
        """Acknowledges a processed enrichment task."""
        await self.client.xack(STREAM_ENRICHMENT_TASKS, GROUP_ENRICHMENT_WORKERS, message_id)

    # ─────────────────────────────────────────────────────────────
    # RECOVERY & AUTOCLAIM
    # ─────────────────────────────────────────────────────────────

    async def autoclaim_abandoned(
        self,
        stream: str,
        group: str,
        consumer_name: str,
        min_idle_time_ms: int = 60000,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """Claims messages pending beyond min_idle_time_ms from dead or stalled workers."""
        try:
            # redis-py xautoclaim returns (next_cursor, [(msg_id, fields), ...], deleted_msg_ids)
            result = await self.client.xautoclaim(
                name=stream,
                groupname=group,
                consumername=consumer_name,
                min_idle_time=min_idle_time_ms,
                start_id="0-0",
                count=count,
            )
            if not result or len(result) < 2:
                return []
            claimed_messages = result[1]
            return [{"id": msg_id, "data": fields} for msg_id, fields in claimed_messages]
        except Exception as e:
            logger.warning(f"Failed to autoclaim on stream '{stream}': {e}")
            return []

    async def get_stream_depth(self, stream: str) -> int:
        """Returns the approximate length of a Redis stream for backpressure monitoring."""
        try:
            return await self.client.xlen(stream)
        except Exception as e:
            logger.warning(f"Failed to inspect stream depth for '{stream}': {e}")
            return 0
