"""
FastUI Playwright Scraper Base
==============================
Deterministic browser lifecycle manager and abstract scraping template.
Guarantees resource cleanup, resource blocking (images/media/fonts),
RSS memory instrumentation, and container memory safety.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, Route, async_playwright

from contracts import DiscoveredLead, DiscoverySearchParams
from core.constants import (
    DEFAULT_USER_AGENT,
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
)
from core.exceptions import BrowserInitializationError
from sources.base import DiscoverySourceAdapter
from utils.memory import memory_tracker

logger = logging.getLogger(__name__)

# Resource types blocked to drastically reduce Chromium memory and network overhead
BLOCKED_RESOURCE_TYPES = {"image", "media", "font", "websocket"}

# Domains/keywords to abort (analytics, trackers, heavy ads)
BLOCKED_URL_PATTERNS = (
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "facebook.net",
    "analytics",
    "tracker",
    "ads",
)


async def _route_interceptor(route: Route) -> None:
    """Blocks non-essential resources to optimize memory and speed."""
    request = route.request
    resource_type = request.resource_type
    url = request.url.lower()

    if resource_type in BLOCKED_RESOURCE_TYPES:
        await route.abort()
        return

    if any(pattern in url for pattern in BLOCKED_URL_PATTERNS):
        await route.abort()
        return

    await route.continue_()


class PlaywrightScraper(DiscoverySourceAdapter, ABC):
    """
    Abstract base class providing deterministic headless Chromium browser lifecycle management.
    Ensures exactly one browser/context/page per discovery operation and guaranteed cleanup.
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        self.is_exhausted: bool = False

    async def _init_browser(self) -> None:
        """Launches headless Chromium with container-safe low-memory arguments."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-zygote",
                    "--disable-background-networking",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-breakpad",
                    "--disable-component-extensions-with-background-pages",
                    "--disable-extensions",
                    "--disable-ipc-flooding-protection",
                    "--disable-renderer-backgrounding",
                    "--disable-blink-features=AutomationControlled",
                    "--js-flags=--max-old-space-size=512",
                ],
            )
        except Exception as e:
            await self._cleanup_resources()
            raise BrowserInitializationError(f"Failed to launch browser: {e}") from e

    async def _cleanup_resources(self) -> None:
        """
        Deterministically closes Page -> Context -> Browser -> Playwright hierarchy
        and executes garbage collection to release OS and Python memory buffers.
        """
        # 1. Close Page
        if self.page:
            try:
                if not self.page.is_closed():
                    await self.page.close()
            except Exception as e:
                logger.debug(f"Notice closing page: {e}")
            finally:
                self.page = None

        # 2. Close BrowserContext
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.debug(f"Notice closing context: {e}")
            finally:
                self.context = None

        # 3. Close Browser
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.debug(f"Notice closing browser: {e}")
            finally:
                self.browser = None

        # 4. Stop Playwright
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.debug(f"Notice stopping playwright: {e}")
            finally:
                self.playwright = None

        # 5. Release Python memory objects
        memory_tracker.force_garbage_collection()

    @abstractmethod
    async def extract_leads(self, page: Page, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """Subclasses extract leads from the loaded page."""
        pass

    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """
        Executes discovery workflow with guaranteed browser lifecycle cleanup and RSS instrumentation.
        """
        source_name = getattr(self, "source_name", self.__class__.__name__)
        memory_tracker.log_stage("discovery_start", source=source_name)

        try:
            await self._init_browser()
            if not self.browser:
                raise BrowserInitializationError("Browser failed to initialize.")

            self.context = await self.browser.new_context(
                viewport={"width": DEFAULT_VIEWPORT_WIDTH, "height": DEFAULT_VIEWPORT_HEIGHT},
                user_agent=DEFAULT_USER_AGENT,
            )

            # Auto-close any unexpectedly spawned popup pages to prevent memory leaks
            self.context.on("page", lambda p: asyncio.create_task(p.close()))

            # Enable resource blocking
            await self.context.route("**/*", _route_interceptor)

            self.page = await self.context.new_page()

            memory_tracker.log_stage(
                "browser_started",
                source=source_name,
                active_contexts=1,
                active_pages=1,
            )

            logger.info(f"Starting discovery for '{params.target_audience}' in '{params.location}' (limit={params.limit})")
            leads = await self.extract_leads(self.page, params)
            return leads

        except Exception as e:
            logger.error(f"Playwright discovery failed on {source_name}: {e}", exc_info=True)
            raise
        finally:
            memory_tracker.log_stage("before_cleanup", source=source_name)
            await self._cleanup_resources()
            memory_tracker.log_stage("after_cleanup", source=source_name)
