"""
FastUI Worker Subsystem
========================
Standalone worker entrypoint and scraper execution daemon.
"""

import asyncio
import logging
import os
import sys

# Ensure both services and services/api directories are on path
SERVICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api"))

for path in [SERVICES_DIR, API_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from worker.contracts import DiscoverySearchParams
    from worker.sources.aggregator import MultiSourceDiscoveryAggregator
except ImportError:
    from contracts import DiscoverySearchParams
    from sources.aggregator import MultiSourceDiscoveryAggregator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fastui.worker")


class ScraperWorkerDaemon:
    """
    Dedicated worker daemon responsible for data discovery and headless scraping workflows.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.aggregator = MultiSourceDiscoveryAggregator(headless=headless)

    async def execute_discovery(self, target_audience: str, location: str, limit: int = 20):
        """
        Executes a direct discovery scrape run.
        """
        params = DiscoverySearchParams(
            target_audience=target_audience,
            location=location,
            limit=limit,
        )
        logger.info(f"Worker executing discovery for '{params.target_audience}' in '{params.location}' (limit: {limit})")
        return await self.aggregator.discover(params)

    async def run(self) -> None:
        """Starts worker listener / health daemon."""
        logger.info("FastUI Scraper Worker daemon initialized and ready.")


async def main():
    worker = ScraperWorkerDaemon(headless=True)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
