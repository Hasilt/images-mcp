from __future__ import annotations

import httpx

from stock_image_mcp.attribution import format_attribution
from stock_image_mcp.models import ImageResult, ProviderName
from stock_image_mcp.providers.pexels import PexelsProvider
from stock_image_mcp.providers.unsplash import UnsplashProvider


def _result(provider: ProviderName) -> ImageResult:
    return ImageResult(
        id="1",
        provider=provider,
        url="https://example.com/img.jpg",
        thumbnail_url="https://example.com/img-thumb.jpg",
        photographer_name="Alex",
        license="Test License",
        attribution_required=False,
        source_page_url="https://example.com/page",
    )


def test_format_attribution_dispatches_to_correct_provider() -> None:
    client = httpx.AsyncClient()
    providers = {
        ProviderName.PEXELS: PexelsProvider("key", client),
        ProviderName.UNSPLASH: UnsplashProvider("key", client),
    }

    pexels_text = format_attribution(_result(ProviderName.PEXELS), providers)
    unsplash_text = format_attribution(_result(ProviderName.UNSPLASH), providers)

    assert "Pexels" in pexels_text
    assert "Unsplash" in unsplash_text
    assert "Alex" in pexels_text
    assert "Alex" in unsplash_text
