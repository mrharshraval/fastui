import asyncio
import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus
from playwright.async_api import Page

try:
    from worker.contracts import DiscoverySearchParams, DiscoveredLead
except ImportError:
    from contracts import DiscoverySearchParams, DiscoveredLead
from .playwright_base import PlaywrightScraper

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
    # Normalize narrow no-break spaces (\u202f), non-breaking spaces (\xa0), zero-width spaces (\u200b)
    return text.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u200b', ' ').strip()

def extract_phone_number(text: str) -> Optional[str]:
    cleaned = clean_unicode_spaces(text)
    if not cleaned:
        return None
    candidates = PHONE_REGEX.findall(cleaned)
    for c in candidates:
        c_clean = c.strip()
        digits = sum(ch.isdigit() for ch in c_clean)
        # Valid phone numbers have 8 to 15 digits
        if 8 <= digits <= 15:
            # Exclude 4-digit/8-digit year patterns like 2024 or 1999
            if not (c_clean.startswith(('19', '20')) and digits <= 8):
                return c_clean
    return None

class GoogleMapsScraper(PlaywrightScraper):
    """
    Scrapes Google Maps for business listings based on target audience and location parameters.
    """
    
    async def extract_leads(self, page: Page, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        target_audience = params.target_audience.strip()
        location = params.location.strip()
        
        search_query = f"{target_audience} in {location}".strip()
        if not search_query or search_query == "in":
            search_query = target_audience or location or "Businesses"
            
        encoded_query = quote_plus(search_query)
        url = f"https://www.google.com/maps/search/{encoded_query}"
        
        logger.info(f"Navigating to {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.warning(f"Navigation notice: {e}")
        
        # Handle Google Consent popup if present
        try:
            consent_btn = await page.query_selector('button[aria-label*="Accept all"], button[aria-label*="Agree"]')
            if consent_btn:
                await consent_btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Wait for the results feed to render
        feed_selector = 'div[role="feed"]'
        try:
            await page.wait_for_selector(feed_selector, timeout=12000)
        except Exception:
            logger.info("Feed container not detected by role='feed', checking fallback selectors...")
            try:
                await page.wait_for_selector('div[role="article"], a[href*="/maps/place/"]', timeout=8000)
            except Exception:
                logger.warning(f"No listings rendered for query '{search_query}'.")
                return []
            
        # Smooth scroll down to load search items
        try:
            await page.evaluate(f'''
                const feed = document.querySelector('{feed_selector}');
                if (feed) {{
                    feed.scrollTop = feed.scrollHeight;
                }}
            ''')
            await asyncio.sleep(1.5)
        except Exception:
            pass
        
        leads: List[DiscoveredLead] = []
        articles = await page.query_selector_all('div[role="article"]')
        if not articles:
            articles = await page.query_selector_all('div.Nv2PK')
        
        max_items = min(params.limit, 25)
        for article in articles[:max_items]:
            try:
                # 1. Extract business name
                name_element = await article.query_selector('div.fontHeadlineSmall, div.qBF1Pd, .qBF1Pd')
                if not name_element:
                    continue
                name = clean_unicode_spaces(await name_element.inner_text())
                if not name:
                    continue
                    
                # 2. Extract textual content for phone and details
                raw_text = await article.inner_text()
                text_content = clean_unicode_spaces(raw_text)
                
                phone = extract_phone_number(text_content)
                website = None
                category = target_audience if target_audience else "Business"
                
                address = None
                
                # Check for explicit website link in card
                website_link = await article.query_selector('a[data-value="Website"], a[aria-label*="website" i]')
                if website_link:
                    href = await website_link.get_attribute("href")
                    if href:
                        website = href
                
                # If website or phone missing from card summary, check place detail pane
                link_el = await article.query_selector('a.hfpxzc, a[href*="/maps/place/"]')
                if link_el:
                    try:
                        if not phone or not website:
                            await link_el.click()
                            await asyncio.sleep(1.2)

                            # Extract phone from detail pane
                            if not phone:
                                phone_el = await page.query_selector(
                                    'button[data-item-id*="phone"], button[aria-label*="Phone" i], button[data-tooltip*="phone" i], [data-item-id*="phone"]'
                                )
                                if phone_el:
                                    phone_aria = clean_unicode_spaces(await phone_el.get_attribute("aria-label") or "")
                                    phone_txt = clean_unicode_spaces(await phone_el.inner_text() or "")
                                    phone = extract_phone_number(phone_aria or phone_txt)

                            # Extract website from detail pane
                            if not website:
                                web_el = await page.query_selector(
                                    'a[data-item-id*="authority"], a[aria-label*="Website" i], a[data-tooltip*="website" i]'
                                )
                                if web_el:
                                    website = await web_el.get_attribute("href")
                                    
                            # Extract address from detail pane
                            addr_el = await page.query_selector(
                                'button[data-item-id*="address"], button[aria-label*="Address:" i], button[data-tooltip*="address" i]'
                            )
                            if addr_el:
                                addr_aria = clean_unicode_spaces(await addr_el.get_attribute("aria-label") or "")
                                addr_txt = clean_unicode_spaces(await addr_el.inner_text() or "")
                                full_addr = (addr_aria or addr_txt).replace("Address:", "").strip()
                                if full_addr:
                                    address = full_addr
                    except Exception as e:
                        logger.debug(f"Detail pane extraction skipped for {name}: {e}")

                leads.append(DiscoveredLead(
                    name=name,
                    category=category,
                    city=location,
                    address=address,
                    phone=phone,
                    website=website,
                    source_platform="google_maps",
                    source_url=url
                ))
                
            except Exception as e:
                logger.debug(f"Skipped article: {e}")
                
        logger.info(f"Extracted {len(leads)} leads from Google Maps for '{search_query}'")
        return leads
