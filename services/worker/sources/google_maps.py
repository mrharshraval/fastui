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


from utils.phone import normalize_global_phone


def extract_phone_number(text: str, location: Optional[str] = None) -> Optional[str]:
    cleaned = clean_unicode_spaces(text)
    if not cleaned:
        return None
    candidates = PHONE_REGEX.findall(cleaned)
    for c in candidates:
        c_clean = c.strip()
        digits = sum(ch.isdigit() for c in c_clean)
        if 8 <= digits <= 15:
            if not (c_clean.startswith(('19', '20')) and digits <= 8):
                display_phone, _ = normalize_global_phone(c_clean, location=location)
                return display_phone
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
                consent_btn = await page.query_selector(
                    'button[aria-label*="Accept all"], button[aria-label*="Agree"], form[action*="consent"] button, button:has-text("Accept all"), button:has-text("I agree")'
                )
                if consent_btn:
                    await consent_btn.click()
                    await asyncio.sleep(0.8)
            except Exception:
                pass

            # Wait for results feed with graceful timeout
            feed_selector = 'div[role="feed"]'
            has_feed = True
            try:
                await page.wait_for_selector(feed_selector, timeout=6000)
            except Exception:
                try:
                    await page.wait_for_selector('div[role="article"], div.Nv2PK, a[href*="/maps/place/"]', timeout=4000)
                except Exception:
                    has_feed = False
                    logger.info(f"No listings rendered for query '{search_query}'.")
                    continue

            # Auto-scroll loop to load listings up to remaining target
            scroll_attempts = 0
            max_scroll_attempts = 15
            previous_count = 0

            for _ in range(max_scroll_attempts):
                if len(leads) >= target_limit or not memory_tracker.is_memory_safe():
                    break

                # Count current cards
                card_count = await page.evaluate('''() => {
                    return document.querySelectorAll('div[role="article"], div.Nv2PK, a.hfpxzc').length;
                }''')

                if card_count >= (target_limit - len(leads)):
                    break

                if card_count == previous_count:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:
                        break
                else:
                    scroll_attempts = 0

                previous_count = card_count

                # Scroll the feed or main scrollable container
                scrolled = await page.evaluate('''() => {
                    const selectors = [
                        'div[role="feed"]',
                        'div.m6QErb[aria-label*="Results for"]',
                        'div.m6QErb.DxyBCb',
                        'div.m6QErb',
                        'div[role="main"]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.scrollHeight > el.clientHeight) {
                            el.scrollTop = el.scrollHeight;
                            return true;
                        }
                    }
                    window.scrollTo(0, document.body.scrollHeight);
                    return false;
                }''')

                await asyncio.sleep(1.2)

            # Check if Google Maps redirected to a single place page
            current_url = page.url
            if "/maps/place/" in current_url:
                single_lead_data = await page.evaluate('''() => {
                    const nameEl = document.querySelector('h1.DUwDvf, h1.fontHeadlineLarge, h1');
                    const name = nameEl ? nameEl.innerText.trim() : null;
                    if (!name) return null;

                    const webEl = document.querySelector('a[data-item-id="authority"], a[aria-label*="website" i]');
                    const website = webEl ? webEl.href : null;

                    const phoneEl = document.querySelector('button[data-item-id*="phone"], button[aria-label*="Phone" i]');
                    let phone = null;
                    if (phoneEl) {
                        phone = phoneEl.getAttribute('aria-label') || phoneEl.innerText;
                    }

                    const addrEl = document.querySelector('button[data-item-id*="address"], button[aria-label*="Address" i]');
                    let address = null;
                    if (addrEl) {
                        address = (addrEl.getAttribute('aria-label') || addrEl.innerText || '').replace(/^Address:\s*/i, '').trim();
                    }

                    return { name, website, phone, address };
                }''')

                if single_lead_data and single_lead_data.get("name"):
                    s_name = clean_unicode_spaces(single_lead_data["name"])
                    if s_name.lower() not in seen_names:
                        seen_names.add(s_name.lower())
                        leads.append(DiscoveredLead(
                            name=s_name,
                            category=target_audience if target_audience else "Business",
                            city=location,
                            address=clean_unicode_spaces(single_lead_data.get("address") or ""),
                            phone=extract_phone_number(single_lead_data.get("phone") or "", location=location),
                            website=single_lead_data.get("website"),
                            source_platform="google_maps",
                            source_place_id=extract_place_id(current_url),
                            source_url=current_url,
                        ))
                continue

            # Batch extract all listing cards directly via evaluate
            raw_listings = await page.evaluate('''() => {
                const items = [];
                const cards = document.querySelectorAll('div.Nv2PK, div[role="article"]');

                for (const card of cards) {
                    try {
                        const nameEl = card.querySelector('div.fontHeadlineSmall, div.qBF1Pd, .qBF1Pd, a.hfpxzc');
                        let name = '';
                        if (nameEl) {
                            name = nameEl.innerText ? nameEl.innerText.trim() : (nameEl.getAttribute('aria-label') || '').trim();
                        }
                        if (!name || name.length < 2) continue;

                        let href = '';
                        const linkEl = card.querySelector('a.hfpxzc, a[href*="/maps/place/"]');
                        if (linkEl) {
                            href = linkEl.getAttribute('href') || '';
                        }

                        let website = '';
                        const webEl = card.querySelector('a[data-value="Website"], a[aria-label*="website" i], a[data-item-id="authority"]');
                        if (webEl) {
                            website = webEl.getAttribute('href') || '';
                        }

                        // Collect all text from sub-containers for address, category & phone parsing
                        const textBlobs = [];
                        const textEls = card.querySelectorAll('div.W4Efsd, span.fontBodyMedium');
                        for (const tel of textEls) {
                            if (tel.innerText) {
                                textBlobs.push(tel.innerText.trim());
                            }
                        }

                        const fullText = card.innerText || '';

                        items.push({
                            name,
                            href,
                            website,
                            textBlobs,
                            fullText
                        });
                    } catch (e) {}
                }
                return items;
            }''')

            for item in raw_listings:
                if len(leads) >= target_limit or not memory_tracker.is_memory_safe():
                    break

                try:
                    name = clean_unicode_spaces(item.get("name", ""))
                    if not name or name.lower() in seen_names:
                        continue

                    full_text = clean_unicode_spaces(item.get("fullText", ""))
                    phone = extract_phone_number(full_text, location=location)
                    
                    # Try text blobs if phone not found in full text
                    if not phone:
                        for blob in item.get("textBlobs", []):
                            phone = extract_phone_number(blob, location=location)
                            if phone:
                                break

                    website = item.get("website") or None
                    place_href = item.get("href") or None
                    source_place_id = extract_place_id(place_href)

                    # Extract address from text blobs
                    address = None
                    for blob in item.get("textBlobs", []):
                        # Address blobs usually contain commas or location keywords and are distinct from review counts
                        if any(c.isdigit() for c in blob) and len(blob) > 10 and not blob.startswith(('(', '★', 'http')):
                            address = clean_unicode_spaces(blob)
                            break

                    seen_names.add(name.lower())
                    leads.append(DiscoveredLead(
                        name=name,
                        category=target_audience if target_audience else "Business",
                        city=location,
                        address=address,
                        phone=phone,
                        website=website,
                        source_platform="google_maps",
                        source_place_id=source_place_id,
                        source_url=place_href or url,
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")

        # Mark source exhausted if fewer leads found than target limit across all queries
        if len(leads) < target_limit:
            self.is_exhausted = True

        logger.info(f"GoogleMapsScraper extracted {len(leads)} leads (exhausted={self.is_exhausted})")
        return leads
