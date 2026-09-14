"""
Unit tests for shared retry decorator.
Verifies retry attempts, backoff, exception filtering, and cancellation awareness.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from shared.retry import retry_async


@pytest.mark.asyncio
async def test_retry_async_succeeds_first_attempt():
    mock_func = AsyncMock(return_value="success")
    decorated = retry_async(max_retries=3, base_delay=0.01)(mock_func)

    res = await decorated()
    assert res == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_async_retries_on_specified_exception():
    mock_func = AsyncMock(side_effect=[ConnectionError("Temporary failure"), "recovered"])
    decorated = retry_async(max_retries=3, base_delay=0.01, exceptions=(ConnectionError,))(mock_func)

    res = await decorated()
    assert res == "recovered"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_async_raises_after_max_retries():
    mock_func = AsyncMock(side_effect=TimeoutError("Permanent timeout"))
    decorated = retry_async(max_retries=2, base_delay=0.01, exceptions=(TimeoutError,))(mock_func)

    with pytest.raises(TimeoutError):
        await decorated()
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_async_never_catches_cancellation():
    mock_func = AsyncMock(side_effect=asyncio.CancelledError())
    decorated = retry_async(max_retries=3, base_delay=0.01)(mock_func)

    with pytest.raises(asyncio.CancelledError):
        await decorated()
    assert mock_func.call_count == 1
