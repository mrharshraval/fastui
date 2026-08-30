import pytest
from core.retry import retry_async

@pytest.mark.asyncio
async def test_retry_success_after_failure():
    attempts = 0

    @retry_async(max_retries=3, base_delay=0.01, backoff_factor=1.5)
    async def flaky_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Temporary failure")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert attempts == 3

@pytest.mark.asyncio
async def test_retry_exhaustion():
    @retry_async(max_retries=2, base_delay=0.01)
    async def always_failing():
        raise RuntimeError("Permanent error")

    with pytest.raises(RuntimeError):
        await always_failing()
