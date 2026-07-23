"""Fans a search out across all configured providers concurrently."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from stock_image_mcp.models import ImageResult, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider
from stock_image_mcp.rate_limiter import RateLimiter, RateLimitExceeded

logger = logging.getLogger(__name__)


@dataclass
class ProviderSearchOutcome:
    provider: ProviderName
    results: list[ImageResult]
    skipped_reason: str | None = None


async def search_provider(
    provider: ImageProvider, params: SearchParams, rate_limiter: RateLimiter
) -> ProviderSearchOutcome:
    if not provider.configured:
        return ProviderSearchOutcome(
            provider.name, [], skipped_reason="not configured (no API key)"
        )

    try:
        await rate_limiter.acquire(provider.name)
    except RateLimitExceeded as exc:
        return ProviderSearchOutcome(provider.name, [], skipped_reason=str(exc))

    try:
        results = await provider.search(params)
    except Exception as exc:  # noqa: BLE001 - one provider's failure must not sink the rest
        logger.warning("Provider %s search failed: %s", provider.name, exc, exc_info=True)
        return ProviderSearchOutcome(provider.name, [], skipped_reason=f"error: {exc}")

    return ProviderSearchOutcome(provider.name, results)


async def search_all(
    providers: dict[ProviderName, ImageProvider],
    params: SearchParams,
    rate_limiter: RateLimiter,
) -> dict[ProviderName, ProviderSearchOutcome]:
    outcomes = await asyncio.gather(
        *(search_provider(provider, params, rate_limiter) for provider in providers.values())
    )
    return {outcome.provider: outcome for outcome in outcomes}
