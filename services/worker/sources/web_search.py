import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus, unquote

from playwright.async_api import Page

from contracts import DiscoveredLead, DiscoverySearchParams
from sources.playwright_base import PlaywrightScraper
from utils.memory import memory_tracker

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(
    r'(?:(?:\+|0{0,2})\d{1,4}[\s.-]*)?'
    r'(?:\(?\d{2,5}\)?[\s.-]*)?'
    r'\d{3,5}[\s.-]?\d{3,5}'
)


def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u200b', ' ').strip()


class WebSearchScraper(PlaywrightScraper):
    """
    Scrapes DuckDuckGo HTML search results to discover business websites,
    contact emails, and phone numbers.
    """

    source_name = "web_search"

    async def extract_leads(self, page: Page, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        target_audience = params.target_audience.strip()
        location = params.location.strip()
        target_limit = params.limit if params.limit and params.limit > 0 else 50

        search_query = f"{target_audience} {location} contact website phone".strip()
        encoded_query = quote_plus(search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        logger.info(f"WebSearchScraper: Searching for '{search_query}' (limit={target_limit})")
        memory_tracker.log_stage("source_navigation", source=self.source_name, extra={"query": search_query})

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            logger.warning(f"WebSearch navigation error: {e}")
            self.is_exhausted = True
            return []

        leads: List[DiscoveredLead] = []
        self.is_exhausted = False

        try:
            results = await page.query_selector_all('div.result, div.web-result, .results_links')
            if not results:
                results = await page.query_selector_all('a.result__url, a.result__snippet')

            for res in results[:target_limit]:
                if len(leads) >= target_limit or not memory_tracker.is_memory_safe():
                    break

                try:
                    title_el = await res.query_selector('a.result__a, h2 a, a')
                    if not title_el:
                        continue

                    raw_title = clean_text(await title_el.inner_text())
                    name = re.split(r'[:|•\-]', raw_title)[0].strip()
                    if not name or len(name) < 3:
                        continue

                    href = await title_el.get_attribute("href")
                    website: Optional[str] = None
                    if href and "duckduckgo.com/l/?" in href:
                        match = re.search(r'uddg=([^&]+)', href)
                        if match:
                            website = unquote(match.group(1))
                    elif href and href.startswith("http"):
                        website = href

                    if website and any(agg in website.lower() for agg in ["duckduckgo", "google.", "wikipedia", "youtube", "facebook.com/search"]):
                        continue

                    snippet_el = await res.query_selector('.result__snippet, .snippet')
                    snippet_text = clean_text(await snippet_el.inner_text()) if snippet_el else ""

                    email: Optional[str] = None
                    emails = EMAIL_REGEX.findall(snippet_text)
                    if emails:
                        email = emails[0]

                    phone: Optional[str] = None
                    phones = PHONE_REGEX.findall(snippet_text)
                    for p in phones:
                        p_clean = p.strip()
                        digits = sum(ch.isdigit() for ch in p_clean)
                        if 8 <= digits <= 15 and not p_clean.startswith(('19', '20')):
                            phone = p_clean
                            break

                    leads.append(DiscoveredLead(
                        name=name,
                        category=target_audience or "Business",
                        city=location,
                        website=website,
                        phone=phone,
                        email=email,
                        source_platform="web_search",
                        source_url=website or url
                    ))
                except Exception as e:
                    logger.debug(f"WebSearch skipped item: {e}")

        except Exception as e:
            logger.warning(f"WebSearch extraction error: {e}")

        if len(leads) < target_limit:
            self.is_exhausted = True

        logger.info(f"WebSearchScraper extracted {len(leads)} leads (exhausted={self.is_exhausted})")
        return leads
