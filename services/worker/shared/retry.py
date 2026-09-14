"""
FastUI Worker Retry Helper
==========================
Async retry decorator with exponential backoff, randomized full jitter,
and cancellation awareness.
"""

import asyncio
import functools
import logging
import random
from typing import Callable, Tuple, Type, Union

logger = logging.getLogger("fastui.worker.retry")

DEFAULT_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    TimeoutError,
    ConnectionError,
    OSError,
)


def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = DEFAULT_RETRYABLE_EXCEPTIONS,
):
    """
    Decorator for retrying async operations with exponential backoff and full jitter.
    Never intercepts or retries asyncio.CancelledError.
    """
    if isinstance(exceptions, type):
        retry_exceptions = (exceptions,)
    else:
        retry_exceptions = tuple(exceptions)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except asyncio.CancelledError:
                    # Cooperative cancellation must never be swallowed or retried
                    raise
                except retry_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Operation '{func.__name__}' failed after {max_retries} attempts: {e}"
                        )
                        raise

                    # Exponential backoff with full jitter
                    delay = min(delay * backoff_factor, max_delay)
                    jittered_delay = delay * random.uniform(0.5, 1.0)
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} of '{func.__name__}' failed: {e}. "
                        f"Retrying in {jittered_delay:.2f}s..."
                    )
                    await asyncio.sleep(jittered_delay)

            if last_exception:
                raise last_exception

        return wrapper

    return decorator
