"""
FastUI Social Media Intelligence Extractor
==========================================
Discovers verified social media profile links explicitly associated
with the official business website.
"""

from typing import Dict
from urllib.parse import urlparse

from bs4 import BeautifulSoup

KNOWN_SOCIAL_DOMAINS = {
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "twitter.com": "twitter",
    "x.com": "twitter",
}

SHARING_INTENTS = (
    "sharer.php",
    "intent/tweet",
    "sharearticle",
    "share.php",
    "share?",
    "dialog/share",
    "pin/create",
)


def extract_social_links(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extracts explicit social profile URLs from HTML links.
    """
    social_profiles: Dict[str, str] = {}

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        href_lower = href.lower()

        # Reject sharing widgets and intents
        if any(intent in href_lower for intent in SHARING_INTENTS):
            continue

        if href.startswith("//"):
            href = f"https:{href}"
        elif not href.startswith(("http://", "https://")):
            # Check if it starts with domain directly, e.g. "instagram.com/clinic"
            if any(d in href_lower for d in KNOWN_SOCIAL_DOMAINS):
                href = f"https://{href}"
            else:
                continue

        try:
            parsed = urlparse(href)
            netloc = parsed.netloc.lower().replace("www.", "")

            for domain, platform in KNOWN_SOCIAL_DOMAINS.items():
                if domain in netloc:
                    path = parsed.path.strip("/")
                    # Ensure path is an actual profile/channel, not generic home, feed, or policy link
                    if (
                        path
                        and len(path) > 1
                        and not path.startswith(
                            (
                                "home",
                                "terms",
                                "privacy",
                                "about",
                                "policies",
                                "help",
                                "login",
                                "watch",
                                "feed",
                                "explore",
                                "shorts",
                            )
                        )
                    ):
                        if platform not in social_profiles:
                            scheme = parsed.scheme or "https"
                            full_url = f"{scheme}://{netloc}/{path}"
                            if parsed.query and "profile.php" in path:
                                full_url = f"{full_url}?{parsed.query}"
                            social_profiles[platform] = full_url
                    break
        except Exception:
            continue

    return social_profiles
