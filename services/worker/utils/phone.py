"""
Universal Global Phone Number Normalizer & Country Code Resolver
================================================================
Handles domestic trunk prefixes (e.g., leading '0'), international dialing prefixes,
and standardizes phone numbers with country calling codes across all global locations.
"""

import re
from typing import Optional, Tuple

# Comprehensive mapping of country names, aliases, and ISO codes to calling codes
COUNTRY_CALLING_CODES = {
    # South Asia
    "india": "91", "in": "91", "gujarat": "91", "maharashtra": "91", "delhi": "91",
    "karnataka": "91", "tamil nadu": "91", "telangana": "91", "uttar pradesh": "91",
    "rajasthan": "91", "punjab": "91", "kerala": "91", "west bengal": "91",
    "ahmedabad": "91", "mumbai": "91", "pune": "91", "bangalore": "91", "bengaluru": "91",
    "chennai": "91", "hyderabad": "91", "kolkata": "91", "surat": "91", "jaipur": "91",
    "pakistan": "92", "pk": "92",
    "bangladesh": "93", "bd": "880",
    "sri lanka": "94", "lk": "94",
    "nepal": "977", "np": "977",

    # North America
    "united states": "1", "usa": "1", "us": "1", "america": "1",
    "canada": "1", "ca": "1",

    # Europe & UK
    "united kingdom": "44", "uk": "44", "gb": "44", "great britain": "44",
    "england": "44", "scotland": "44", "wales": "44", "london": "44",
    "germany": "49", "de": "49", "deutschland": "49", "berlin": "49",
    "france": "33", "fr": "33", "paris": "33",
    "italy": "39", "it": "39", "rome": "39", "milan": "39",
    "spain": "34", "es": "34", "madrid": "34", "barcelona": "34",
    "netherlands": "31", "nl": "31", "amsterdam": "31",
    "switzerland": "41", "ch": "41", "zurich": "41",
    "belgium": "32", "be": "32",
    "austria": "43", "at": "43",
    "sweden": "46", "se": "46",
    "norway": "47", "no": "47",
    "denmark": "45", "dk": "45",
    "finland": "358", "fi": "358",
    "ireland": "353", "ie": "353",
    "poland": "48", "pl": "48",
    "portugal": "351", "pt": "351",
    "greece": "30", "gr": "30",
    "czech republic": "420", "cz": "420",
    "romania": "40", "ro": "40",
    "hungary": "36", "hu": "36",
    "turkey": "90", "tr": "90",
    "russia": "7", "ru": "7",

    # Middle East
    "united arab emirates": "971", "uae": "971", "ae": "971", "dubai": "971", "abu dhabi": "971",
    "saudi arabia": "966", "sa": "966", "ksa": "966", "riyadh": "966", "jeddah": "966",
    "qatar": "974", "qa": "974", "doha": "974",
    "kuwait": "965", "kw": "965",
    "oman": "968", "om": "968",
    "bahrain": "973", "bh": "973",
    "israel": "972", "il": "972",
    "singapore": "65", "sg": "65",

    # Asia Pacific
    "australia": "61", "au": "61", "sydney": "61", "melbourne": "61", "brisbane": "61",
    "new zealand": "64", "nz": "64", "auckland": "64",
    "japan": "81", "jp": "81", "tokyo": "81",
    "south korea": "82", "kr": "82", "seoul": "82",
    "china": "86", "cn": "86", "hong kong": "852", "hk": "852",
    "malaysia": "60", "my": "60", "kuala lumpur": "60",
    "indonesia": "62", "id": "62", "jakarta": "62",
    "thailand": "66", "th": "66", "bangkok": "66",
    "philippines": "63", "ph": "63", "manila": "63",
    "vietnam": "84", "vn": "84",

    # Africa & Latin America
    "south africa": "27", "za": "27", "johannesburg": "27",
    "nigeria": "234", "ng": "234", "lagos": "234",
    "kenya": "254", "ke": "254", "nairobi": "254",
    "egypt": "20", "eg": "20", "cairo": "20",
    "brazil": "55", "br": "55", "sao paulo": "55",
    "mexico": "52", "mx": "52",
    "argentina": "54", "ar": "54",
    "chile": "56", "cl": "56",
    "colombia": "57", "co": "57",
}


def resolve_country_code(location: Optional[str]) -> str:
    """
    Extracts the international calling code from a location string.
    Defaults to '91' (India) if unspecified or unrecognized.
    """
    if not location:
        return "91"

    loc_lower = location.lower()
    # Split by comma or whitespace to inspect tokens
    tokens = [t.strip() for t in re.split(r'[,/|\-]+', loc_lower) if t.strip()]

    # 1. Match specific token from right-to-left (Country is usually at the end)
    for token in reversed(tokens):
        if token in COUNTRY_CALLING_CODES:
            return COUNTRY_CALLING_CODES[token]

    # 2. Match substring search
    for name, code in COUNTRY_CALLING_CODES.items():
        if len(name) > 2 and name in loc_lower:
            return code

    return "91"


def normalize_global_phone(
    raw_phone: Optional[str],
    location: Optional[str] = None,
    default_country_code: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Standardizes a phone number for any country in the world.
    - Removes trunk leading '0' or '00'
    - Prepends target country code
    - Returns a tuple of: (formatted_display_phone, e164_canonical_phone)
      Example: ('+91 79 2640 1234', '+917926401234')
    """
    if not raw_phone or not isinstance(raw_phone, str):
        return None, None

    # Clean non-digit characters
    digits = re.sub(r"\D", "", raw_phone)
    if not digits or len(digits) < 5:
        return None, None

    target_cc = default_country_code or resolve_country_code(location)

    # 1. Handle international prefix '00' (e.g., 00919822012345 -> 919822012345)
    if digits.startswith("00") and len(digits) > 8:
        digits = digits[2:]

    # 2. Check if raw phone explicitly had a '+' sign with a valid country code
    has_plus = raw_phone.strip().startswith("+")

    if has_plus:
        # Number already has country code
        # Check if digits start with target_cc or any known cc
        pass
    else:
        # Check if starts with leading '0' (domestic trunk prefix)
        if digits.startswith("0"):
            # Strip single leading 0 (or multiple leading zeros)
            digits = digits.lstrip("0")
            digits = f"{target_cc}{digits}"
        elif not digits.startswith(target_cc):
            # No leading 0, and doesn't already start with country code
            # e.g., 9822012345 in India -> 919822012345
            digits = f"{target_cc}{digits}"

    e164 = f"+{digits}"

    # 3. Build human-readable formatted display phone
    formatted = _format_e164_display(digits, target_cc)
    return formatted, e164


def _format_e164_display(digits: str, target_cc: str) -> str:
    """Formats raw digits into international formatted layout with spaces."""
    if digits.startswith("91") and len(digits) == 12:  # India (+91)
        sub = digits[2:]
        if sub[0] in "6789":  # Mobile: +91 98220 12345
            return f"+91 {sub[:5]} {sub[5:]}"
        elif sub.startswith(("11", "22", "33", "44", "20", "79", "80")):  # 2-digit STD: +91 79 2640 1234
            return f"+91 {sub[:2]} {sub[2:6]} {sub[6:]}"
        else:  # 3-digit STD: +91 265 234 5678
            return f"+91 {sub[:3]} {sub[3:6]} {sub[6:]}"

    elif digits.startswith("1") and len(digits) == 11:  # US/Canada (+1)
        return f"+1 {digits[1:4]} {digits[4:7]} {digits[7:]}"

    elif digits.startswith("44") and len(digits) in (12, 13):  # UK (+44)
        sub = digits[2:]
        return f"+44 {sub[:4]} {sub[4:]}"

    elif digits.startswith("971") and len(digits) in (11, 12):  # UAE (+971)
        sub = digits[3:]
        return f"+971 {sub[:2]} {sub[2:5]} {sub[5:]}"

    elif digits.startswith("61") and len(digits) == 11:  # Australia (+61)
        sub = digits[2:]
        return f"+61 {sub[0]} {sub[1:5]} {sub[5:]}"

    # General standard fallback
    if len(digits) > len(target_cc):
        cc_len = len(target_cc)
        return f"+{digits[:cc_len]} {digits[cc_len:]}"

    return f"+{digits}"
