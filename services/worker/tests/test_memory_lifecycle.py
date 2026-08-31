"""
FastUI Worker Memory & Lifecycle Tests
======================================
Tests deterministic browser lifecycle, memory tracking, cleanup on success/failure/timeout,
and resource management.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from contracts import DiscoverySearchParams
from sources.playwright_base import PlaywrightScraper
from utils.memory import MemoryTracker, memory_tracker


class DummyScraper(PlaywrightScraper):
    source_name = "dummy_test_source"

    def __init__(self, headless: bool = True, behavior: str = "success") -> None:
        super().__init__(headless=headless)
        self.behavior = behavior

    async def extract_leads(self, page, params):
        if self.behavior == "exception":
            raise RuntimeError("Extraction unexpected crash")
        if self.behavior == "timeout":
            raise asyncio.TimeoutError("Extraction timed out")
        return []


def test_memory_tracker_metrics_and_logging(caplog):
    tracker = MemoryTracker(safety_limit_mb=800.0)
    rss = tracker.get_total_rss_mb()
    assert rss >= 0.0
    assert tracker.is_memory_safe() is True

    with caplog.at_level("INFO"):
        tracker.log_stage(
            "test_stage",
            source="test_source",
            batch=1,
            new_count=10,
            active_contexts=1,
            active_pages=1,
        )

    log_text = caplog.text
    assert "MEMORY test_stage" in log_text
    assert "source=test_source" in log_text
    assert "batch=1" in log_text
    assert "new=10" in log_text
    assert "contexts=1" in log_text
    assert "pages=1" in log_text


def test_memory_tracker_safety_threshold():
    tracker = MemoryTracker(safety_limit_mb=50.0)
    with patch.object(tracker, "get_total_rss_mb", return_value=60.0):
        assert tracker.is_memory_safe() is False


@pytest.mark.asyncio
async def test_scraper_cleanup_on_success():
    scraper = DummyScraper(behavior="success")

    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()

    mock_page.is_closed = MagicMock(return_value=False)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("sources.playwright_base.async_playwright") as mock_ap:
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright)

        params = DiscoverySearchParams(target_audience="Dentist", location="Ahmedabad", limit=10)
        leads = await scraper.discover(params)

        assert leads == []
        mock_page.close.assert_awaited_once()
        mock_context.close.assert_awaited_once()
        mock_browser.close.assert_awaited_once()
        mock_playwright.stop.assert_awaited_once()
        assert scraper.page is None
        assert scraper.context is None
        assert scraper.browser is None
        assert scraper.playwright is None


@pytest.mark.asyncio
async def test_scraper_cleanup_on_exception():
    scraper = DummyScraper(behavior="exception")

    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()

    mock_page.is_closed = MagicMock(return_value=False)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("sources.playwright_base.async_playwright") as mock_ap:
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright)

        params = DiscoverySearchParams(target_audience="Dentist", location="Ahmedabad", limit=10)
        with pytest.raises(RuntimeError, match="Extraction unexpected crash"):
            await scraper.discover(params)

        mock_page.close.assert_awaited_once()
        mock_context.close.assert_awaited_once()
        mock_browser.close.assert_awaited_once()
        mock_playwright.stop.assert_awaited_once()
        assert scraper.page is None
        assert scraper.context is None
        assert scraper.browser is None


@pytest.mark.asyncio
async def test_scraper_cleanup_on_timeout():
    scraper = DummyScraper(behavior="timeout")

    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()

    mock_page.is_closed = MagicMock(return_value=False)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("sources.playwright_base.async_playwright") as mock_ap:
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright)

        params = DiscoverySearchParams(target_audience="Dentist", location="Ahmedabad", limit=10)
        with pytest.raises(asyncio.TimeoutError):
            await scraper.discover(params)

        mock_page.close.assert_awaited_once()
        mock_context.close.assert_awaited_once()
        mock_browser.close.assert_awaited_once()
        mock_playwright.stop.assert_awaited_once()
