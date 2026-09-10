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


from utils.phone import normalize_global_phone, is_mobile_phone, get_whatsapp_url


def extract_phone_number(text: str, location: Optional[str] = None) -> Optional[str]:
    cleaned = clean_unicode_spaces(text)
    if not cleaned:
        return None
    candidates = PHONE_REGEX.findall(cleaned)
    for c in candidates:
        c_clean = c.strip()
        digits = sum(c.isdigit() for c in c_clean)
        if 8 <= digits <= 15:
            if not (c_clean.startswith(('19', '20')) and digits <= 8):
                display_phone, _ = normalize_global_phone(c_clean, location=location)
                return display_phone
    return None


def extract_place_id(url: Optional[str], card_attrs: Optional[dict] = None) -> Optional[str]:
    """
    Extracts canonical Google Maps place identification from URL or card attributes.
    Returns:
      - 'ChIJ...' if standard Places API token is found.
      - '0x...:0x...' canonical place hex identifier if found.
      - Decimal Google CID if found in query parameters.
      - None if uncertain. NEVER falls back to returning the business text name.
    """
    if url:
        # 1. Check for ChIJ... Google Place ID in URL
        match_chij = re.search(r'(ChIJ[a-zA-Z0-9_-]{23,})', url)
        if match_chij:
            return match_chij.group(1)

        # 2. Check for canonical place hex identifier: !1s(0x...:0x...)
        match_hex = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', url)
        if match_hex:
            return match_hex.group(1)

        # 3. Explicit cid query parameter in URL (e.g. ?cid=5746927495034872712)
        match_cid = re.search(r'[?&]cid=(\d+)', url)
        if match_cid:
            return match_cid.group(1)

    if card_attrs:
        for attr in ("data-result-id", "data-cid", "data-place-id"):
            val = card_attrs.get(attr)
            if val and (val.startswith("0x") or val.startswith("ChIJ") or len(val) >= 16):
                return val.strip()

    return None


def extract_decimal_cid(url: Optional[str]) -> Optional[str]:
    """
    Converts the secondary 64-bit hex token from a Google Maps URL into the standard decimal CID.
    Example: !1s0x395e848aba5bd449:0x4fc14db35ff0a388 -> 5746927495034872712
    """
    if not url:
        return None

    # If already a decimal CID parameter
    match_cid = re.search(r'[?&]cid=(\d+)', url)
    if match_cid:
        return match_cid.group(1)

    # Secondary hex token in !1s0x...:0x... or standalone 0x...:0x...
    match_hex = re.search(r'(?:!1s)?0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)', url)
    if match_hex:
        try:
            return str(int(match_hex.group(1), 16))
        except ValueError:
            pass

    return None


def build_canonical_place_url(url: Optional[str]) -> Optional[str]:
    """
    Builds an authoritative, verified canonical Google Maps place URL for an individual business.
    Strictly rejects search query URLs and search camera viewports.
    Returns:
      - 'https://www.google.com/maps?cid={cid}' if decimal CID is derived.
      - 'https://www.google.com/maps/place/...' if valid place URL.
      - None if unverified or if the URL is a search results URL.
    """
    if not url:
        return None

    lower_url = url.lower()
    # Strictly reject search query URLs that are not place URLs
    if "/maps/search/" in lower_url and "/maps/place/" not in lower_url:
        return None

    decimal_cid = extract_decimal_cid(url)
    if decimal_cid:
        return f"https://www.google.com/maps?cid={decimal_cid}"

    if "/maps/place/" in url:
        clean_url = url.split("?")[0].rstrip("/")
        return clean_url

    return None


def extract_coordinates(url: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    """
    Parses latitude and longitude from Google Maps place URL or parameters.
    CRITICAL: Strictly prioritizes true physical pin locations (!8m2!3d and !3d).
    STRICTLY REJECTS search camera viewport coordinates (/@lat,lng) to prevent
    viewport center collision across business records.
    Validates numeric ranges: -90 <= lat <= 90, -180 <= lng <= 180.
    """
    if not url:
        return None, None

    lower_url = url.lower()
    # If this is purely a search URL, reject all coordinates
    if "/maps/search/" in lower_url and "/maps/place/" not in lower_url:
        return None, None

    # Priority 1: !8m2!3d<lat>!4d<lng> (Standard Google Maps pin location in place URLs)
    match_8m2 = re.search(r'!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match_8m2:
        try:
            lat = float(match_8m2.group(1))
            lng = float(match_8m2.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                return lat, lng
        except ValueError:
            pass

    # Priority 2: !3d<lat>!4d<lng> (Direct 3D pin location)
    match_3d4d = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match_3d4d:
        try:
            lat = float(match_3d4d.group(1))
            lng = float(match_3d4d.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                return lat, lng
        except ValueError:
            pass

    # Priority 3: Explicit place query parameters (e.g. ?query=lat,lng or &ll=lat,lng) on place URLs
    if "/maps/place/" in lower_url or "cid=" in lower_url:
        match_query_loc = re.search(r'[?&](?:query|ll|loc)=(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match_query_loc:
            try:
                lat = float(match_query_loc.group(1))
                lng = float(match_query_loc.group(2))
                if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                    return lat, lng
            except ValueError:
                pass

    # Note: /@lat,lng is deliberately NOT parsed here because in Google Maps place URLs
    # and search URLs, /@lat,lng represents the map CAMERA VIEWPORT, not the business pin.
    return None, None


class GoogleMapsScraper(PlaywrightScraper):
    """
    Scrapes Google Maps for business listings based on target audience and location.
    Bounded memory footprint, auto-scrolls feed, extracts place IDs, coordinates,
    ratings, reviews, actual categories, and handles query variations.
    """

    source_name = "google_maps"

    def __init__(self, headless: bool = True) -> None:
        super().__init__(headless=headless)
        self.next_cursor: Optional[str] = None
        self.current_locality: Optional[str] = None
        self.localities_remaining: Optional[int] = None

    def _generate_locality_queries(self, target_audience: str, locality: str, city: str) -> List[str]:
        """
        Generates diversified queries pairing the active locality with category and specialty keywords
        to surface businesses categorized under varied Google Maps taxonomy tags.
        """
        base_city = city.split(",")[0].strip()
        loc_clean = locality.strip()

        if base_city.lower() in loc_clean.lower():
            geo_term = loc_clean
        else:
            geo_term = f"{loc_clean}, {base_city}"

        primary = f"{target_audience} in {geo_term}".strip()
        variations = [primary]

        audience_clean = target_audience.lower().strip()
        if "dental" in audience_clean or "dentist" in audience_clean:
            variations.extend([
                f"Dental Clinic in {geo_term}",
                f"Dentist in {geo_term}",
                f"Dental Hospital in {geo_term}",
            ])
        elif "doctor" in audience_clean or "clinic" in audience_clean or "hospital" in audience_clean:
            variations.extend([
                f"Clinic in {geo_term}",
                f"Hospital in {geo_term}",
                f"Doctor in {geo_term}",
            ])
        elif "restaurant" in audience_clean or "cafe" in audience_clean or "food" in audience_clean:
            variations.extend([
                f"Restaurants in {geo_term}",
                f"Cafes in {geo_term}",
            ])
        else:
            variations.append(f"{target_audience} near {geo_term}")

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

        # 1. Geographic / Locality Subdivision
        from geo.localities import resolve_city_localities

        localities = resolve_city_localities(location)
        if not localities:
            localities = [location]

        locality_idx = 0
        if params.cursor and params.cursor.startswith("loc:"):
            try:
                locality_idx = int(params.cursor.split(":")[1])
            except (ValueError, IndexError):
                locality_idx = 0

        if locality_idx >= len(localities):
            self.is_exhausted = True
            self.next_cursor = None
            self.current_locality = None
            self.localities_remaining = 0
            logger.info(f"All {len(localities)} localities in '{location}' exhausted.")
            return []

        active_locality = localities[locality_idx]
        self.current_locality = active_locality
        self.localities_remaining = max(0, len(localities) - (locality_idx + 1))
        self.next_cursor = f"loc:{locality_idx + 1}" if (locality_idx + 1 < len(localities)) else None

        logger.info(
            f"GoogleMapsScraper: Active locality [{locality_idx+1}/{len(localities)}] '{active_locality}' "
            f"for location '{location}' (cursor={params.cursor}, next={self.next_cursor})"
        )

        # 2. Query Diversification for the active locality
        queries = params.query_variations or self._generate_locality_queries(target_audience, active_locality, location)
        if not queries:
            queries = [f"{target_audience} in {active_locality}, {location}".strip()]

        leads: List[DiscoveredLead] = []
        seen_keys = set()
        self.is_exhausted = False

        for query_idx, search_query in enumerate(queries):
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
            try:
                await page.wait_for_selector(feed_selector, timeout=6000)
            except Exception:
                try:
                    await page.wait_for_selector('div[role="article"], div.Nv2PK, a[href*="/maps/place/"]', timeout=4000)
                except Exception:
                    logger.info(f"No listings rendered for query '{search_query}'.")
                    continue

            # 3. Deep Result-Feed Exploration & Unbounded Discovery
            # Explore the feed continuously until genuine exhaustion (Google's end marker or DOM growth halts)
            consecutive_no_growth = 0
            max_scroll_attempts = 35
            previous_count = 0

            for scroll_idx in range(max_scroll_attempts):
                if not memory_tracker.is_memory_safe():
                    logger.warning("Memory safety ceiling reached during scroll. Stopping feed exploration.")
                    break

                # Check for authentic Google Maps end-of-feed marker
                is_end_of_feed = await page.evaluate('''() => {
                    const endMarker = document.querySelector('div.HlvSq, div.fontTitleMedium.HlvSq, span.HlvSq');
                    if (endMarker) return true;
                    const feed = document.querySelector('div[role="feed"]');
                    if (feed && feed.innerText.includes("You've reached the end of the list")) return true;
                    return false;
                }''')
                if is_end_of_feed:
                    logger.info(f"Query '{search_query}': Authentic end-of-list encountered.")
                    break

                # Count current cards
                card_count = await page.evaluate('''() => {
                    return document.querySelectorAll('div[role="article"], div.Nv2PK, a.hfpxzc').length;
                }''')

                if card_count == previous_count:
                    consecutive_no_growth += 1
                    if consecutive_no_growth >= 4:
                        logger.info(f"Query '{search_query}': Feed settled after {scroll_idx} scrolls ({card_count} cards).")
                        break
                else:
                    consecutive_no_growth = 0

                previous_count = card_count

                # Scroll the feed or main scrollable container
                await page.evaluate('''() => {
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

                await asyncio.sleep(0.9)

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

                    let rating = null;
                    const ratingEl = document.querySelector('div.F7nice span[aria-hidden="true"], span.ceNzKf, span.MW4etd');
                    if (ratingEl) {
                        const m = (ratingEl.innerText || '').match(/([1-5]\.[0-9])/);
                        if (m) rating = parseFloat(m[1]);
                    }

                    let reviewsCount = null;
                    const revEl = document.querySelector('div.F7nice span[aria-label*="review" i], span.UY7F9, button[aria-label*="review" i]');
                    if (revEl) {
                        const m = (revEl.getAttribute('aria-label') || revEl.innerText || '').replace(/,/g, '').match(/(\d+)/);
                        if (m) reviewsCount = parseInt(m[1], 10);
                    }

                    let category = null;
                    const catEl = document.querySelector('button.DkEaL, button[jsaction*="category"], span.fontBodyMedium');
                    if (catEl && catEl.innerText) {
                        category = catEl.innerText.trim();
                    }

                    let openingHours = null;
                    const hoursEl = document.querySelector('div.t39EBf, table.eKjhWe, button[data-item-id*="oh"]');
                    if (hoursEl) {
                        openingHours = (hoursEl.innerText || '').replace(/\s+/g, ' ').trim();
                    }

                    return { name, website, phone, address, rating, reviewsCount, category, openingHours };
                }''')

                if single_lead_data and single_lead_data.get("name"):
                    s_name = clean_unicode_spaces(single_lead_data["name"])
                    lat, lng = extract_coordinates(current_url)
                    true_place_id = extract_place_id(current_url)
                    canonical_url = build_canonical_place_url(current_url)
                    s_phone = extract_phone_number(single_lead_data.get("phone") or "", location=location)
                    s_addr = clean_unicode_spaces(single_lead_data.get("address") or "")

                    decimal_cid = extract_decimal_cid(current_url)
                    if decimal_cid:
                        s_key = f"cid:{decimal_cid}"
                    elif true_place_id:
                        s_key = f"pid:{true_place_id}"
                    elif s_phone:
                        s_key = f"phone:{s_phone}"
                    elif s_addr:
                        s_key = f"addr:{s_name.lower()}:{s_addr.lower()}"
                    else:
                        s_key = f"name:{s_name.lower()}:{active_locality.lower()}"

                    if s_key not in seen_keys:
                        seen_keys.add(s_key)

                        s_is_mobile = is_mobile_phone(s_phone, location=location) if s_phone else False
                        s_whatsapp = get_whatsapp_url(s_phone, location=location) if (s_phone and s_is_mobile) else None

                        leads.append(DiscoveredLead(
                            name=s_name,
                            category=single_lead_data.get("category") or target_audience,
                            city=location,
                            address=s_addr or None,
                            phone=s_phone,
                            has_whatsapp=s_is_mobile,
                            whatsapp=s_whatsapp,
                            website=single_lead_data.get("website"),
                            source_platform="google_maps",
                            source_place_id=true_place_id,
                            source_url=canonical_url,
                            rating=single_lead_data.get("rating"),
                            reviews_count=single_lead_data.get("reviewsCount"),
                            latitude=lat,
                            longitude=lng,
                            google_place_id=true_place_id,
                            google_maps_url=canonical_url,
                            opening_hours=single_lead_data.get("openingHours"),
                        ))
                continue

            # 4. Batch extract listing cards from the feed
            raw_listings = await page.evaluate('''() => {
                const items = [];
                const cards = document.querySelectorAll('div.Nv2PK, div[role="article"]');

                for (const card of cards) {
                    try {
                        // 1. Name
                        const nameEl = card.querySelector('div.fontHeadlineSmall, div.qBF1Pd, .qBF1Pd, a.hfpxzc');
                        let name = '';
                        if (nameEl) {
                            name = nameEl.innerText ? nameEl.innerText.trim() : (nameEl.getAttribute('aria-label') || '').trim();
                        }
                        if (!name || name.length < 2) continue;

                        // 2. Google Maps Link
                        let href = '';
                        const linkEl = card.querySelector('a.hfpxzc, a[href*="/maps/place/"]');
                        if (linkEl) {
                            href = linkEl.getAttribute('href') || '';
                        }

                        // 3. Website
                        let website = '';
                        const webEl = card.querySelector('a[data-value="Website"], a[aria-label*="website" i], a[data-item-id="authority"]');
                        if (webEl) {
                            website = webEl.getAttribute('href') || '';
                        }

                        // 4. Rating
                        let rating = null;
                        const ratingEl = card.querySelector('span.MW4etd, span[aria-label*="stars" i], span[role="img"][aria-label*="star" i]');
                        if (ratingEl) {
                            const rText = ratingEl.innerText || ratingEl.getAttribute('aria-label') || '';
                            const match = rText.match(/([1-5]\.[0-9])/);
                            if (match) rating = parseFloat(match[1]);
                        }

                        // 5. Review count
                        let reviewsCount = null;
                        const reviewsEl = card.querySelector('span.UY7F9, span[aria-label*="reviews" i], span[aria-label*="ratings" i]');
                        if (reviewsEl) {
                            const revText = reviewsEl.innerText || reviewsEl.getAttribute('aria-label') || '';
                            const match = revText.replace(/,/g, '').match(/\\(?(\\d+)\\)?/);
                            if (match) reviewsCount = parseInt(match[1], 10);
                        }

                        // 6. Subheader text blobs
                        const textBlobs = [];
                        const textEls = card.querySelectorAll('div.W4Efsd, span.fontBodyMedium');
                        for (const tel of textEls) {
                            if (tel.innerText) {
                                textBlobs.push(tel.innerText.trim());
                            }
                        }

                        // Category extraction
                        let category = null;
                        for (const blob of textBlobs) {
                            const parts = blob.split(/[·•]/).map(p => p.trim());
                            for (const p of parts) {
                                if (p.length > 2 && p.length < 35 && !p.match(/^[0-9.]/) && !p.includes('(') && !p.toLowerCase().includes('open') && !p.toLowerCase().includes('closed')) {
                                    category = p;
                                    break;
                                }
                            }
                            if (category) break;
                        }

                        // Status & Opening hours
                        let status = null;
                        let openingHours = null;
                        const statusEl = card.querySelector('span[style*="color: rgb(217, 48, 37)"], span[style*="color: rgb(24, 128, 56)"]');
                        if (statusEl) {
                            status = statusEl.innerText ? statusEl.innerText.trim() : null;
                        }

                        for (const blob of textBlobs) {
                            if (blob.toLowerCase().includes('open') || blob.toLowerCase().includes('closed')) {
                                openingHours = blob.trim();
                                break;
                            }
                        }

                        const cardAttrs = {
                            "data-result-id": card.getAttribute("data-result-id") || "",
                            "data-cid": card.getAttribute("data-cid") || "",
                            "data-fid": card.getAttribute("data-fid") || "",
                        };

                        const fullText = card.innerText || '';

                        items.push({
                            name,
                            href,
                            website,
                            rating,
                            reviewsCount,
                            category,
                            status,
                            openingHours,
                            cardAttrs,
                            textBlobs,
                            fullText
                        });
                    } catch (e) {}
                }
                return items;
            }''')

            # 5. Strict 5-Link Location Verification Chain (Business → Place → URL → Address → Coordinate)
            for item in raw_listings:
                if not memory_tracker.is_memory_safe():
                    break

                try:
                    name = clean_unicode_spaces(item.get("name", ""))
                    if not name or len(name) < 2:
                        continue

                    full_text = clean_unicode_spaces(item.get("fullText", ""))
                    phone = extract_phone_number(full_text, location=location)

                    if not phone:
                        for blob in item.get("textBlobs", []):
                            phone = extract_phone_number(blob, location=location)
                            if phone:
                                break

                    website = item.get("website") or None
                    place_href = item.get("href") or None
                    card_attrs = item.get("cardAttrs") or {}

                    # Link 1 & 2: Canonical Google Maps place identification
                    true_place_id = extract_place_id(place_href, card_attrs=card_attrs)
                    decimal_cid = extract_decimal_cid(place_href)

                    # Link 3: Canonical place URL (strictly rejects search URLs)
                    canonical_url = build_canonical_place_url(place_href)

                    # Link 4: Verified physical pin coordinates (strictly rejects /@lat,lng viewport camera)
                    lat, lng = extract_coordinates(place_href)

                    # Link 5: Verified address extraction
                    address = None
                    for blob in item.get("textBlobs", []):
                        b_clean = clean_unicode_spaces(blob)
                        b_lower = b_clean.lower()
                        if any(reject in b_lower for reject in ("review", "open", "close", "pm", "am", "★", "http", "ratings")):
                            continue
                        if PHONE_REGEX.search(b_clean):
                            continue
                        if re.match(r'^[0-9.,() ]+$', b_clean):
                            continue
                        if len(b_clean) > 8 and (any(c.isdigit() for c in b_clean) or "," in b_clean):
                            if b_clean != item.get("category"):
                                address = b_clean
                                break

                    category = item.get("category") or target_audience or "Dental Clinic"
                    rating = item.get("rating")
                    reviews_count = item.get("reviewsCount")
                    opening_hours = item.get("openingHours")
                    business_status = item.get("status")

                    # Deduplication key based on canonical identification
                    if decimal_cid:
                        item_key = f"cid:{decimal_cid}"
                    elif true_place_id:
                        item_key = f"pid:{true_place_id}"
                    elif canonical_url:
                        item_key = f"url:{canonical_url}"
                    elif phone:
                        item_key = f"phone:{phone}"
                    elif address:
                        item_key = f"addr:{name.lower()}:{address.lower()}"
                    else:
                        item_key = f"name:{name.lower()}:{active_locality.lower()}"

                    if item_key in seen_keys:
                        continue
                    seen_keys.add(item_key)

                    is_mobile = is_mobile_phone(phone, location=location) if phone else False
                    has_whatsapp = is_mobile or any(
                        "whatsapp" in (blob or "").lower() or "wa.me" in (blob or "").lower()
                        for blob in item.get("textBlobs", [])
                    )
                    whatsapp_val = get_whatsapp_url(phone, location=location) if (phone and has_whatsapp) else None

                    # Strict 5-Link Verification Rule:
                    # Stored google_maps_url, latitude, and longitude must belong exclusively to that verified place.
                    # Under NO circumstances is a search results page URL or viewport coordinate assigned.
                    verified_maps_url = canonical_url if canonical_url else None
                    verified_lat = lat if (lat is not None and verified_maps_url) else None
                    verified_lng = lng if (lng is not None and verified_maps_url) else None

                    leads.append(DiscoveredLead(
                        name=name,
                        category=category,
                        city=location,
                        address=address,
                        phone=phone,
                        has_whatsapp=has_whatsapp,
                        whatsapp=whatsapp_val,
                        website=website,
                        source_platform="google_maps",
                        source_place_id=true_place_id or (f"cid:{decimal_cid}" if decimal_cid else None),
                        source_url=verified_maps_url,
                        rating=rating,
                        reviews_count=reviews_count,
                        latitude=verified_lat,
                        longitude=verified_lng,
                        google_place_id=true_place_id or decimal_cid,
                        google_maps_url=verified_maps_url,
                        opening_hours=opening_hours,
                        business_status=business_status,
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")

        # Truly unbounded discovery: return all verified leads without artificial slicing
        if self.localities_remaining == 0:
            self.is_exhausted = True

        logger.info(
            f"GoogleMapsScraper: Extracted {len(leads)} verified leads for locality '{active_locality}' "
            f"(exhausted={self.is_exhausted}, remaining_localities={self.localities_remaining}, next_cursor={self.next_cursor})"
        )
        return leads

