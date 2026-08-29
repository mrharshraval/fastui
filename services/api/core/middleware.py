import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("fastui.access")

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a unique correlation ID (X-Request-ID)
    and logs request method, path, status, and duration in milliseconds.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Attach request_id to request state for access in downstream handlers
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} -> FAILED after {duration_ms}ms: {exc}",
                exc_info=True
            )
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
        )
        return response
