import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright
from worker.contracts import DiscoverySearchParams, DiscoveredLead
from .base import DiscoverySourceAdapter

logger = logging.getLogger(__name__)

class PlaywrightScraper(DiscoverySourceAdapter, ABC):
    """
    Base class for Playwright-based discovery workers with deterministic lifecycle management.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None

    async def _init_browser(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
        except Exception as e:
            await self._close_browser()
            raise e

    async def _close_browser(self):
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
        """
        Subclasses must implement the page extraction logic.
        """
        pass

    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """
        Main entry point for discovery. Guarantees deterministic browser cleanup.
        """
        try:
            await self._init_browser()
            if not self.browser:
                raise RuntimeError("Browser failed to initialize.")
                
            context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()
            
            logger.info(f"Starting discovery for '{params.target_audience}' in '{params.location}'")
            results = await self.extract_leads(page, params)
            return results
            
        except Exception as e:
            logger.error(f"Playwright discovery failed: {e}", exc_info=True)
            raise e
        finally:
            await self._close_browser()
