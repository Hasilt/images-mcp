"""Per-provider in-memory token bucket rate limiting."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from stock_image_mcp.models import ProviderName


class RateLimitExceeded(Exception):
    def __init__(self, provider: ProviderName, retry_after_seconds: float) -> None:
        self.provider = provider
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"{provider} rate limit exceeded; retry after "
            f"{retry_after_seconds:.1f}s or use a different provider"
        )


@dataclass
class _Bucket:
    capacity: int
    window_seconds: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        refill_rate = self.capacity / self.window_seconds  # tokens per second
        self.tokens = min(self.capacity, self.tokens + elapsed * refill_rate)
        self.last_refill = now

    def remaining(self) -> int:
        self._refill()
        return int(self.tokens)

    def time_until_available(self) -> float:
        self._refill()
        if self.tokens >= 1:
            return 0.0
        refill_rate = self.capacity / self.window_seconds
        return (1 - self.tokens) / refill_rate

    def try_consume(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimiter:
    """Token bucket per provider. Max wait before raising is configurable."""

    def __init__(self, max_wait_seconds: float = 5.0) -> None:
        self._buckets: dict[ProviderName, _Bucket] = {}
        self._max_wait_seconds = max_wait_seconds

    def configure(self, provider: ProviderName, limit: int, window_seconds: float) -> None:
        self._buckets[provider] = _Bucket(capacity=limit, window_seconds=window_seconds)

    def remaining(self, provider: ProviderName) -> int:
        bucket = self._buckets.get(provider)
        return bucket.remaining() if bucket else 0

    async def acquire(self, provider: ProviderName) -> None:
        bucket = self._buckets.get(provider)
        if bucket is None:
            return  # provider not rate-limit-configured; nothing to enforce
        if bucket.try_consume():
            return
        wait = bucket.time_until_available()
        if wait > self._max_wait_seconds:
            raise RateLimitExceeded(provider, wait)
        await asyncio.sleep(wait)
        bucket.try_consume()
