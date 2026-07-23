from __future__ import annotations

import httpx

from stock_image_mcp.aggregator import search_all
from stock_image_mcp.models import ImageResult, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider
from stock_image_mcp.rate_limiter import RateLimiter


def _make_result(provider: ProviderName, image_id: str) -> ImageResult:
    return ImageResult(
        id=image_id,
        provider=provider,
        url="https://example.com/img.jpg",
        thumbnail_url="https://example.com/img-thumb.jpg",
        license="Test License",
        attribution_required=False,
        source_page_url="https://example.com/page",
    )


class FakeProvider(ImageProvider):
    def __init__(self, name: ProviderName, api_key: str | None, *, raises: bool = False) -> None:
        super().__init__(api_key, httpx.AsyncClient())
        self.name = name
        self._raises = raises
        self.requires_api_key = True

    async def search(self, params: SearchParams) -> list[ImageResult]:
        if self._raises:
            raise RuntimeError("provider is down")
        return [_make_result(self.name, "1")]

    def build_attribution(self, image: ImageResult) -> str:
        return f"credit for {image.provider}"


async def test_search_all_skips_unconfigured_provider() -> None:
    providers = {
        ProviderName.PEXELS: FakeProvider(ProviderName.PEXELS, api_key=None),
        ProviderName.UNSPLASH: FakeProvider(ProviderName.UNSPLASH, api_key="key"),
    }
    outcomes = await search_all(providers, SearchParams(query="cat"), RateLimiter())

    assert outcomes[ProviderName.PEXELS].skipped_reason == "not configured (no API key)"
    assert outcomes[ProviderName.UNSPLASH].results[0].id == "1"


async def test_search_all_tolerates_provider_failure() -> None:
    providers = {
        ProviderName.PEXELS: FakeProvider(ProviderName.PEXELS, api_key="key", raises=True),
        ProviderName.UNSPLASH: FakeProvider(ProviderName.UNSPLASH, api_key="key"),
    }
    outcomes = await search_all(providers, SearchParams(query="cat"), RateLimiter())

    assert outcomes[ProviderName.PEXELS].results == []
    assert "error" in (outcomes[ProviderName.PEXELS].skipped_reason or "")
    assert outcomes[ProviderName.UNSPLASH].results[0].id == "1"


async def test_search_all_reports_rate_limit_exceeded() -> None:
    limiter = RateLimiter(max_wait_seconds=0.0)
    limiter.configure(ProviderName.PEXELS, limit=1, window_seconds=3600)
    await limiter.acquire(ProviderName.PEXELS)  # exhaust the single token
    providers = {ProviderName.PEXELS: FakeProvider(ProviderName.PEXELS, api_key="key")}

    outcomes = await search_all(providers, SearchParams(query="cat"), limiter)

    assert outcomes[ProviderName.PEXELS].results == []
    assert "rate limit" in (outcomes[ProviderName.PEXELS].skipped_reason or "").lower()
