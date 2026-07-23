from __future__ import annotations

import pytest

from stock_image_mcp.models import ProviderName
from stock_image_mcp.rate_limiter import RateLimiter, RateLimitExceeded


async def test_unconfigured_provider_never_limited() -> None:
    limiter = RateLimiter()
    for _ in range(100):
        await limiter.acquire(ProviderName.PEXELS)  # no configure() call


async def test_consumes_tokens_within_capacity() -> None:
    limiter = RateLimiter(max_wait_seconds=0.01)
    limiter.configure(ProviderName.PEXELS, limit=3, window_seconds=3600)

    for _ in range(3):
        await limiter.acquire(ProviderName.PEXELS)

    assert limiter.remaining(ProviderName.PEXELS) == 0


async def test_raises_when_exceeded_and_wait_too_long() -> None:
    limiter = RateLimiter(max_wait_seconds=0.01)
    limiter.configure(ProviderName.PEXELS, limit=1, window_seconds=3600)

    await limiter.acquire(ProviderName.PEXELS)
    with pytest.raises(RateLimitExceeded):
        await limiter.acquire(ProviderName.PEXELS)


async def test_waits_and_succeeds_when_refill_is_fast_enough() -> None:
    limiter = RateLimiter(max_wait_seconds=1.0)
    limiter.configure(ProviderName.PEXELS, limit=1, window_seconds=0.1)

    await limiter.acquire(ProviderName.PEXELS)
    await limiter.acquire(ProviderName.PEXELS)  # should wait briefly, then succeed


def test_remaining_reflects_capacity_before_use() -> None:
    limiter = RateLimiter()
    limiter.configure(ProviderName.UNSPLASH, limit=50, window_seconds=3600)
    assert limiter.remaining(ProviderName.UNSPLASH) == 50
