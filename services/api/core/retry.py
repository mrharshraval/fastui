"""
FastUI Async Retry Utility
==========================
"""

import asyncio
import functools
import logging
from typing import Callable, Tuple, Type, Union

logger = logging.getLogger(__name__)


def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
):
    """
    Decorator for retrying async functions with exponential backoff.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_retries} attempts: {e}"
                        )
                        raise e

                    logger.warning(
                        f"Attempt {attempt}/{max_retries} for '{func.__name__}' failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            if last_exception:
                raise last_exception
        return wrapper
    return decorator
