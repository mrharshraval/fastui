"""
FastUI Worker Core Constants
============================
Scraper defaults, timeouts, viewports, and browser headers.
"""

DEFAULT_VIEWPORT_WIDTH: int = 1280
DEFAULT_VIEWPORT_HEIGHT: int = 800

DEFAULT_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_SCRAPE_LIMIT: int = 20
MAX_SCRAPE_LIMIT: int = 100
PAGE_NAVIGATION_TIMEOUT_MS: int = 30000
