"""
FastUI Core Constants
=====================
Application-wide constant definitions and limits.
"""

# Pagination Defaults
DEFAULT_PAGE_OFFSET: int = 0
DEFAULT_PAGE_LIMIT: int = 100
MAX_PAGE_LIMIT: int = 500

# Authentication & Security
DEFAULT_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
CORRELATION_ID_HEADER: str = "X-Request-ID"
AUTH_COOKIE_NAME: str = "access_token"

# Export Limits
MAX_EXPORT_ROWS: int = 10000
CSV_CHUNK_SIZE: int = 500
