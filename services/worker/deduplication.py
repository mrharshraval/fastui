import re
from urllib.parse import urlparse
from typing import Optional
from sqlalchemy import select, or_, and_, func
from models.schema import Business

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes a phone number to canonical E.164-style standard format (+<digits>).
    Strips all whitespace, hyphens, parentheses, and non-numeric characters.
    Defaults 10-digit Indian numbers to +91 country code.
    
    Examples:
    - "+91 98765 00001" -> "+919876500001"
    - "(415) 555-1234"   -> "+914155551234" (if 10 digits) or "+14155551234" (if 11 digits with country code)
    - "+1 (415) 555-1234" -> "+14155551234"
    """
    if not phone or not isinstance(phone, str):
        return None
        
    digits = re.sub(r'\D', '', phone)
    if not digits:
        return None
        
    # Handle leading 0 (e.g. 07046335733 -> 10-digit Indian number)
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) == 10:
        return f"+91{digits}"
    return f"+{digits}"

def normalize_website(website: Optional[str]) -> Optional[str]:
    """
    Normalizes a website URL to its canonical base hostname.
    Strips protocols, www subdomains, port numbers, paths, query strings, and fragments.
    
    Examples:
    - "https://www.Example.COM/services?ref=1" -> "example.com"
    - "http://sub.domain.co.in:8080/" -> "sub.domain.co.in"
    """
    if not website or not isinstance(website, str):
        return None
        
    clean_web = website.strip().lower()
    if not clean_web.startswith(('http://', 'https://')):
        clean_web = 'http://' + clean_web
        
    try:
        parsed = urlparse(clean_web)
        hostname = parsed.hostname or ""
        hostname = re.sub(r'^www\.', '', hostname)
        return hostname.strip() if hostname.strip() else None
    except Exception:
        # Fallback simple regex cleanup
        cleaned = re.sub(r'^https?://', '', website.lower().strip())
        cleaned = re.sub(r'^www\.', '', cleaned)
        cleaned = cleaned.split('/')[0].split('?')[0].split('#')[0].split(':')[0]
        return cleaned if cleaned else None

async def is_duplicate(
    session,
    normalized_phone: Optional[str],
    normalized_website: Optional[str],
    business_name: str,
    city: Optional[str]
) -> bool:
    """
    Checks if a business already exists based on deduplication signals.
    Priority:
    1. Exact normalized website domain
    2. Exact normalized phone
    3. Exact business name + city (case-insensitive exact match)
    
    Returns True if a duplicate is found in the database.
    """
    conditions = []
    
    if normalized_website:
        conditions.append(Business.normalized_website == normalized_website)
    
    if normalized_phone:
        conditions.append(Business.normalized_phone == normalized_phone)
        
    clean_name = business_name.strip() if business_name else ""
    clean_city = city.strip() if city else ""
    
    if clean_name and clean_city:
        conditions.append(
            and_(
                func.lower(Business.business_name) == clean_name.lower(),
                func.lower(Business.city) == clean_city.lower()
            )
        )
    elif clean_name and not normalized_website and not normalized_phone:
        conditions.append(
            func.lower(Business.business_name) == clean_name.lower()
        )
        
    if not conditions:
        return False
        
    query = select(Business.id).where(or_(*conditions)).limit(1)
    result = await session.execute(query)
    duplicate_id = result.scalar_one_or_none()
    
    return duplicate_id is not None

