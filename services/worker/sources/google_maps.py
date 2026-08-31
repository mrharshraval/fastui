import asyncio
import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus, unquote

from playwright.async_api import Page

from contracts import DiscoveredLead, DiscoverySearchParams
from sources.playwright_base import PlaywrightScraper
from utils.memory import memory_tracker

logger = logging.getLogger(__name__)

# International and domestic phone number pattern
PHONE_REGEX = re.compile(
    r'(?:(?:\+|0{0,2})\d{1,4}[\s.-]*)?'
    r'(?:\(?\d{2,5}\)?[\s.-]*)?'
    r'\d{3,5}[\s.-]?\d{3,5}'
)


def clean_unicode_spaces(text: str) -> str:
    if not text:
        return ""
    return text.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u200b', ' ').strip()


def extract_phone_number(text: str) -> Optional[str]:
    cleaned = clean_unicode_spaces(text)
    if not cleaned:
        return None
    candidates = PHONE_REGEX.findall(cleaned)
    for c in candidates:
        c_clean = c.strip()
        digits = sum(ch.isdigit() for ch in c_clean)
        if 8 <= digits <= 15:
            if not (c_clean.startswith(('19', '20')) and digits <= 8):
                return c_clean
    return None


def extract_place_id(url: Optional[str]) -> Optional[str]:
    """Extracts place_id or unique hex place token from Google Maps URL if available."""
    if not url:
        return None
    # Check for !1s0x...:0x... pattern
    match = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', url)
    if match:
        return match.group(1)
    # Check for /place/Name/.../@lat,lng,
    match_place = re.search(r'/maps/place/([^/@]+)', url)
    if match_place:
        return unquote(match_place.group(1)).replace("+", " ").strip()
    return None


class GoogleMapsScraper(PlaywrightScraper):
    """
    Scrapes Google Maps for business listings based on target audience and location.
    Bounded memory footprint, auto-scrolls feed, extracts place IDs, and handles query variations.
    """

    source_name = "google_maps"

    def _generate_query_variations(self, target_audience: str, location: str) -> List[str]:
        """Generates semantic query variations to improve coverage upon feed exhaustion."""
        primary = f"{target_audience} in {location}".strip()
        variations = [primary]

        audience_clean = target_audience.lower().strip()
        if "dental" in audience_clean or "dentist" in audience_clean:
            variations.extend([
                f"Dental Clinic in {location}",
                f"Dentist in {location}",
                f"Dental Hospital in {location}",
                f"Dental Care in {location}",
            ])
        elif "doctor" in audience_clean or "clinic" in audience_clean or "hospital" in audience_clean:
            variations.extend([
                f"Clinic in {location}",
                f"Hospital in {location}",
                f"Healthcare in {location}",
            ])
        elif "restaurant" in audience_clean or "cafe" in audience_clean:
            variations.extend([
                f"Restaurants in {location}",
                f"Cafes in {location}",
                f"Food in {location}",
            ])
        else:
            variations.append(f"{target_audience} near {location}")

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for v in variations:
            if v and v.lower() not in seen:
                seen.add(v.lower())
                deduped.append(v)
        return deduped

    async def extract_leads(self, page: Page, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        target_audience = params.target_audience.strip()
        location = params.location.strip()
        target_limit = params.limit if params.limit and params.limit > 0 else 50

        # Query variations support
        queries = params.query_variations or self._generate_query_variations(target_audience, location)
        if not queries:
            queries = [f"{target_audience} in {location}".strip()]

        leads: List[DiscoveredLead] = []
        seen_names = set()
        self.is_exhausted = False

        for query_idx, search_query in enumerate(queries):
            if len(leads) >= target_limit:
                break

            if not memory_tracker.is_memory_safe():
                logger.warning("Memory safety limit reached during Google Maps search. Halting further queries.")
                break

            encoded_query = quote_plus(search_query)
            url = f"https://www.google.com/maps/search/{encoded_query}"

            logger.info(f"GoogleMapsScraper: Navigating to query [{query_idx+1}/{len(queries)}] '{search_query}'")
            memory_tracker.log_stage("source_navigation", source=self.source_name, extra={"query": search_query})

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            except Exception as e:
                logger.warning(f"Navigation notice for query '{search_query}': {e}")
                continue

            # Handle Google Consent popup if present
            try:
                consent_btn = await page.query_selector('button[aria-label*="Accept all"], button[aria-label*="Agree"]')
                if consent_btn:
                    await consent_btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            # Wait for results feed
            feed_selector = 'div[role="feed"]'
            try:
                await page.wait_for_selector(feed_selector, timeout=8000)
            except Exception:
                try:
                    await page.wait_for_selector('div[role="article"], a[href*="/maps/place/"]', timeout=4000)
                except Exception:
                    logger.info(f"No listings rendered for query '{search_query}'.")
                    continue

            # Auto-scroll loop to load listings up to remaining target
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 15

            for _ in range(max_scroll_attempts):
                if len(leads) >= target_limit or not memory_tracker.is_memory_safe():
                    break

                articles = await page.query_selector_all('div[role="article"], div.Nv2PK')
                current_count = len(articles)

                if current_count >= (target_limit - len(leads)):
                    break

                if current_count == previous_count:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:
                        break
                else:
                    scroll_attempts = 0

                previous_count = current_count

                # Check if end of list reached
                end_indicator = await page.query_selector("span.HlvSq, div.fontTitleSmall:has-text('reached the end')")
                if end_indicator:
                    break

                try:
                    await page.evaluate(f'''
                        const feed = document.querySelector('{feed_selector}');
                        if (feed) {{
                            feed.scrollTop = feed.scrollHeight;
                        }}
                    ''')
                    await asyncio.sleep(1.0)
                except Exception:
                    break

            # Extract listings
            articles = await page.query_selector_all('div[role="article"], div.Nv2PK')

            for article in articles:
                if len(leads) >= target_limit or not memory_tracker.is_memory_safe():
                    break

                try:
                    name_element = await article.query_selector('div.fontHeadlineSmall, div.qBF1Pd, .qBF1Pd')
                    if not name_element:
                        continue
                    name = clean_unicode_spaces(await name_element.inner_text())
                    if not name or name.lower() in seen_names:
                        continue

                    raw_text = await article.inner_text()
                    text_content = clean_unicode_spaces(raw_text)

                    phone = extract_phone_number(text_content)
                    website = None
                    category = target_audience if target_audience else "Business"
                    address = None
                    source_place_id = None
                    place_href = None

                    website_link = await article.query_selector('a[data-value="Website"], a[aria-label*="website" i]')
                    if website_link:
                        href = await website_link.get_attribute("href")
                        if href:
                            website = href

                    link_el = await article.query_selector('a.hfpxzc, a[href*="/maps/place/"]')
                    if link_el:
                        place_href = await link_el.get_attribute("href")
                        source_place_id = extract_place_id(place_href)

                        # Only click detail pane if vital contact details are missing and under bounded count
                        if not phone or not website:
                            try:
                                await link_el.click()
                                await asyncio.sleep(0.6)

                                if not phone:
                                    phone_el = await page.query_selector(
                                        'button[data-item-id*="phone"], button[aria-label*="Phone" i], [data-item-id*="phone"]'
                                    )
                                    if phone_el:
                                        phone_aria = clean_unicode_spaces(await phone_el.get_attribute("aria-label") or "")
                                        phone_txt = clean_unicode_spaces(await phone_el.inner_text() or "")
                                        phone = extract_phone_number(phone_aria or phone_txt)

                                if not website:
                                    web_el = await page.query_selector(
                                        'a[data-item-id*="authority"], a[aria-label*="Website" i]'
                                    )
                                    if web_el:
                                        website = await web_el.get_attribute("href")

                                addr_el = await page.query_selector(
                                    'button[data-item-id*="address"], button[aria-label*="Address:" i]'
                                )
                                if addr_el:
                                    addr_aria = clean_unicode_spaces(await addr_el.get_attribute("aria-label") or "")
                                    addr_txt = clean_unicode_spaces(await addr_el.inner_text() or "")
                                    full_addr = (addr_aria or addr_txt).replace("Address:", "").strip()
                                    if full_addr:
                                        address = full_addr
                            except Exception as e:
                                logger.debug(f"Detail pane extraction skipped for {name}: {e}")

                    seen_names.add(name.lower())
                    leads.append(DiscoveredLead(
                        name=name,
                        category=category,
                        city=location,
                        address=address,
                        phone=phone,
                        website=website,
                        source_platform="google_maps",
                        source_place_id=source_place_id,
                        source_url=place_href or url,
                    ))

                except Exception as e:
                    logger.debug(f"Skipped article: {e}")

        # Mark source exhausted if fewer leads found than target limit across all queries
        if len(leads) < target_limit:
            self.is_exhausted = True

        logger.info(f"GoogleMapsScraper extracted {len(leads)} leads (exhausted={self.is_exhausted})")
        return leads
