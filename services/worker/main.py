"""
FastUI Worker Runtime Entrypoint
================================
Thin composition root managing Redis-driven consumer lifecycles, graceful
shutdown signals, and connection pool cleanup.
"""

import asyncio
import logging
import signal

from core.logging import setup_worker_logging
from infrastructure.redis.client import close_redis_client
from infrastructure.redis.streams import RedisStreams
from orchestration.discovery import DiscoveryConsumer
from orchestration.enrichment import EnrichmentConsumer
from orchestration.recovery import TaskRecoveryService
from orchestration.results import ResultProcessor
from persistence.db import close_db_engine

setup_worker_logging(service_name="fastui-worker")
logger = logging.getLogger("fastui.worker")


async def main() -> None:
    logger.info("Initializing Redis streams and consumer groups...")
    streams = RedisStreams()
    await streams.ensure_groups()

    discovery_consumer = DiscoveryConsumer(streams=streams)
    result_processor = ResultProcessor(streams=streams)
    enrichment_consumer = EnrichmentConsumer(streams=streams)
    recovery_service = TaskRecoveryService(streams=streams)

    consumers = [discovery_consumer, result_processor, enrichment_consumer, recovery_service]
    stop_event = asyncio.Event()

    def _trigger_shutdown(sig_name: str) -> None:
        logger.info(f"Received signal {sig_name}; initiating graceful shutdown...")
        stop_event.set()
        for c in consumers:
            c.running = False

    # Register OS signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig.name: _trigger_shutdown(s))
        except NotImplementedError:
            signal.signal(sig, lambda _signum, _frame, s=sig.name: _trigger_shutdown(s))

    logger.info("Starting workers: DiscoveryConsumer | ResultProcessor | EnrichmentConsumer | TaskRecoveryService")

    consumer_tasks = [
        asyncio.create_task(discovery_consumer.run(), name="DiscoveryConsumer"),
        asyncio.create_task(result_processor.run(), name="ResultProcessor"),
        asyncio.create_task(enrichment_consumer.run(), name="EnrichmentConsumer"),
        asyncio.create_task(recovery_service.run(), name="TaskRecoveryService"),
    ]

    try:
        done, pending = await asyncio.wait(
            [asyncio.create_task(stop_event.wait()), *consumer_tasks],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for t in pending:
            t.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    finally:
        logger.info("Draining active tasks and closing resource pools...")
        await asyncio.gather(
            discovery_consumer.drain(),
            enrichment_consumer.drain(),
            return_exceptions=True,
        )
        await close_db_engine()
        await close_redis_client()
        logger.info("FastUI Worker shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down worker from keyboard interrupt.")
