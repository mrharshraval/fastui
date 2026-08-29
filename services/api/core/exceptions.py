"""
FastUI Core Exceptions
======================
Centralized domain exception hierarchy with HTTP status code mappings.
"""

from typing import Any, Dict, Optional


class FastUIException(Exception):
    """Base domain exception for all FastUI application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class EntityNotFoundError(FastUIException):
    """Raised when a requested domain entity cannot be found."""

    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} with identifier '{identifier}' was not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"entity": entity, "identifier": str(identifier)},
        )


class ConflictError(FastUIException):
    """Raised when an operation conflicts with the current entity state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class ValidationError(FastUIException):
    """Raised when domain-level payload or state validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="UNPROCESSABLE_ENTITY",
            details=details,
        )


class AuthenticationError(FastUIException):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ScrapingError(FastUIException):
    """Raised when an external scraping source adapter fails."""

    def __init__(self, source: str, message: str):
        super().__init__(
            message=f"Scraper error on source '{source}': {message}",
            status_code=502,
            error_code="SCRAPER_ERROR",
            details={"source": source, "error": message},
        )


# Backward-compatibility aliases
EntityNotFoundException = EntityNotFoundError
ConflictException = ConflictError
ValidationException = ValidationError
ScrapingException = ScrapingError
