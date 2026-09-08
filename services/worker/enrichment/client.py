"""
FastUI Website Enrichment HTTP Client
======================================
Secure, lightweight asynchronous HTTP client with SSRF protection,
redirect limits, response size limits, and robust error handling.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse
from typing import Optional, Tuple

import httpx

logger = logging.getLogger("fastui.worker.enrichment.client")

# Safety limits
MAX_REDIRECTS = 5
DEFAULT_TIMEOUT_SEC = 8.0
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 FastUI-Discovery/1.0"
)


def validate_target_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validates that a URL is safe to fetch (prevents SSRF attacks).
    Blocks private, loopback, link-local, and reserved IP ranges.
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL"

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme: {parsed.scheme}"

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname"

        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            return False, f"SSRF blocked: local or cloud metadata host '{hostname}'"

        # Check IP address resolution
        addr_info = socket.getaddrinfo(hostname, None)
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
            ):
                return False, f"SSRF blocked: private or reserved IP address '{ip_str}'"

        return True, None
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


class EnrichmentHttpClient:
    """
    Asynchronous HTTP client for retrieving prospect website HTML.
    """

    def __init__(self, timeout_sec: float = DEFAULT_TIMEOUT_SEC):
        self.timeout = httpx.Timeout(timeout_sec, connect=4.0)

    async def fetch_html(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetches website HTML safely.
        Returns: (html_text, canonical_url, error_message)
        """
        # Normalize protocol if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        is_safe, err_msg = validate_target_url(url)
        if not is_safe:
            logger.warning(f"Aborting fetch for '{url}': {err_msg}")
            return None, None, err_msg

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=MAX_REDIRECTS,
                verify=False,  # Allow sites with minor self-signed cert issues for public discovery
            ) as client:
                response = await client.get(url, headers=headers)

                # Check status code
                if response.status_code >= 400:
                    return None, str(response.url), f"HTTP {response.status_code}"

                # Content-Type check (skip binary downloads like PDFs, ZIPs, large videos)
                content_type = response.headers.get("content-type", "").lower()
                if content_type and not any(t in content_type for t in ("text/html", "application/xhtml", "text/plain")):
                    return None, str(response.url), f"Skipped non-HTML Content-Type: {content_type}"

                # Response size check
                content_bytes = response.content
                if len(content_bytes) > MAX_RESPONSE_BYTES:
                    content_bytes = content_bytes[:MAX_RESPONSE_BYTES]

                # Decode encoding
                html = response.text
                canonical_url = str(response.url)
                return html, canonical_url, None

        except httpx.TimeoutException:
            return None, url, "Connection timeout"
        except httpx.RequestError as e:
            return None, url, f"Request error: {str(e)}"
        except Exception as e:
            return None, url, f"Unexpected error: {str(e)}"
