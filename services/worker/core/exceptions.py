"""
FastUI Worker Exceptions
========================
Domain exceptions for scraper and extraction workflows.
"""


class WorkerException(Exception):
    """Base exception for all worker failures."""
    pass


class BrowserInitializationError(WorkerException):
    """Raised when headless browser launch or context creation fails."""
    pass


class ExtractionError(WorkerException):
    """Raised when page data extraction encounters an unrecoverable structure error."""
    pass
