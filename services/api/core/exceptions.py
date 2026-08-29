from typing import Any, Dict, Optional

class FastUIException(Exception):
    """Base exception for all FastUI application domain errors."""
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

class EntityNotFoundException(FastUIException):
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} with identifier '{identifier}' was not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"entity": entity, "identifier": str(identifier)}
        )

class ConflictException(FastUIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )

class ValidationException(FastUIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="UNPROCESSABLE_ENTITY",
            details=details
        )

class ScrapingException(FastUIException):
    def __init__(self, source: str, message: str):
        super().__init__(
            message=f"Scraper error on source '{source}': {message}",
            status_code=502,
            error_code="SCRAPER_ERROR",
            details={"source": source, "error": message}
        )
