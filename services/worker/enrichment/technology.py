"""
FastUI Website Technology Intelligence
======================================
Non-invasive detection of CMS, frontend frameworks, and analytics
from public HTML, meta tags, and script references.
"""

from bs4 import BeautifulSoup
from contracts import EnrichedTechnology


def detect_website_technology(soup: BeautifulSoup, html: str) -> EnrichedTechnology:
    """
    Analyzes public markup to identify CMS and technology stack.
    """
    tech = EnrichedTechnology()
    html_lower = html.lower()

    # 1. CMS Detection
    generator_tag = soup.find("meta", attrs={"name": "generator"})
    generator_content = generator_tag.get("content", "").lower() if generator_tag else ""

    if "wordpress" in generator_content or "wp-content" in html_lower or "wp-includes" in html_lower:
        tech.cms = "WordPress"
    elif "wix.com" in html_lower or "_wix_" in html_lower or "wixstatic.com" in html_lower:
        tech.cms = "Wix"
    elif "squarespace" in generator_content or "squarespace.com" in html_lower or "static1.squarespace.com" in html_lower:
        tech.cms = "Squarespace"
    elif "webflow" in generator_content or "assets.webflow.com" in html_lower or "webflow.com" in html_lower:
        tech.cms = "Webflow"
    elif "shopify" in generator_content or "cdn.shopify.com" in html_lower:
        tech.cms = "Shopify"
    elif "joomla" in generator_content or "joomla" in html_lower:
        tech.cms = "Joomla"
    elif "drupal" in generator_content or "drupal" in html_lower:
        tech.cms = "Drupal"

    # 2. Frontend Frameworks
    if "__next_data__" in html_lower or "/_next/" in html_lower:
        tech.frameworks.append("Next.js")
    if "react" in html_lower or "react-dom" in html_lower:
        if "Next.js" not in tech.frameworks:
            tech.frameworks.append("React")
    if "vue" in html_lower or "nuxt" in html_lower:
        tech.frameworks.append("Vue.js")
    if "angular" in html_lower:
        tech.frameworks.append("Angular")
    if "bootstrap" in html_lower:
        tech.frameworks.append("Bootstrap")
    if "tailwind" in html_lower:
        tech.frameworks.append("Tailwind CSS")

    # 3. Analytics & Tracking Providers
    if "googletagmanager.com" in html_lower or "gtag(" in html_lower:
        tech.analytics.append("Google Analytics (GA4/GTM)")
    if "connect.facebook.net" in html_lower or "fbevents.js" in html_lower:
        tech.analytics.append("Meta Pixel")
    if "hotjar.com" in html_lower:
        tech.analytics.append("Hotjar")
    if "clarity.ms" in html_lower:
        tech.analytics.append("Microsoft Clarity")

    return tech
