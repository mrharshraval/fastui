import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.logger import correlation_id_ctx, user_id_ctx

logger = logging.getLogger("fastui.access")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Enterprise middleware ensuring end-to-end request correlation propagation (X-Correlation-ID / X-Request-ID)
    and logging latency, path, method, and status.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # Set thread-safe / async-safe ContextVars
        token_corr = correlation_id_ctx.set(correlation_id)
        token_user = user_id_ctx.set("")

        # Attach to request state for downstream handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"{request.method} {request.url.path} -> FAILED after {duration_ms}ms: {exc}",
                exc_info=True,
            )
            correlation_id_ctx.reset(token_corr)
            user_id_ctx.reset(token_user)
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = correlation_id

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
        )

        correlation_id_ctx.reset(token_corr)
        user_id_ctx.reset(token_user)
        return response
