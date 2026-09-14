"""
FastUI Redis Infrastructure Client
==================================
Connection lifecycle management and singleton Redis client.
"""

import logging
from typing import Optional

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger("fastui.infra.redis")

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Returns the singleton async Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_timeout=15.0,
            socket_connect_timeout=10.0,
            socket_keepalive=True,
            retry_on_timeout=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Gracefully closes the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
            logger.info("Redis connection pool closed.")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}", exc_info=True)
        finally:
            _redis_client = None
