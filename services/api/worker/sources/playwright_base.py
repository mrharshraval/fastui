"""
FastUI Playwright Scraper Base
==============================
Deterministic browser lifecycle manager and abstract scraping template.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from playwright.async_api import Browser, Page, Playwright, async_playwright

try:
    from worker.contracts import DiscoveredLead, DiscoverySearchParams
    from worker.core.constants import (
        DEFAULT_USER_AGENT,
        DEFAULT_VIEWPORT_HEIGHT,
        DEFAULT_VIEWPORT_WIDTH,
    )
    from worker.core.exceptions import BrowserInitializationError
except ImportError:
    from contracts import DiscoveredLead, DiscoverySearchParams
    from core.constants import (
        DEFAULT_USER_AGENT,
        DEFAULT_VIEWPORT_HEIGHT,
        DEFAULT_VIEWPORT_WIDTH,
    )
    from core.exceptions import BrowserInitializationError
from .base import DiscoverySourceAdapter

logger = logging.getLogger(__name__)


class PlaywrightScraper(DiscoverySourceAdapter, ABC):
    """
    Abstract base class providing deterministic headless Chromium browser lifecycle management.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None

    async def _init_browser(self) -> None:
        """Launches headless Chromium with container-safe arguments."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
        except Exception as e:
            await self._close_browser()
            raise BrowserInitializationError(f"Failed to launch browser: {e}") from e

    async def _close_browser(self) -> None:
        """Deterministically terminates browser and playwright instances."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.browser = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
            finally:
                self.playwright = None

    @abstractmethod
    async def extract_leads(self, page: Page, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """Subclasses extract leads from the loaded page."""
        pass

    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """
        Executes discovery workflow with guaranteed browser lifecycle cleanup.
        """
        try:
            await self._init_browser()
            if not self.browser:
                raise BrowserInitializationError("Browser failed to initialize.")

            context = await self.browser.new_context(
                viewport={"width": DEFAULT_VIEWPORT_WIDTH, "height": DEFAULT_VIEWPORT_HEIGHT},
                user_agent=DEFAULT_USER_AGENT,
            )
            page = await context.new_page()

            logger.info(f"Starting discovery for '{params.target_audience}' in '{params.location}'")
            return await self.extract_leads(page, params)

        except Exception as e:
            logger.error(f"Playwright discovery failed: {e}", exc_info=True)
            raise
        finally:
            await self._close_browser()
