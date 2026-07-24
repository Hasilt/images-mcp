from __future__ import annotations

import os

import httpx
import respx

os.environ.setdefault("PEXELS_API_KEY", "test-pexels-key")
os.environ.setdefault("UNSPLASH_ACCESS_KEY", "test-unsplash-key")
os.environ.setdefault("DEFAULT_PROVIDER", "pexels")

from stock_image_mcp import server  # noqa: E402  (env vars must be set first)

_PEXELS_RESPONSE = {
    "photos": [
        {
            "id": 1,
            "width": 100,
            "height": 100,
            "url": "https://www.pexels.com/photo/1",
            "photographer": "Test Photographer",
            "photographer_url": "https://www.pexels.com/@test",
            "alt": "A test photo",
            "src": {
                "original": "https://images.pexels.com/1-original.jpg",
                "tiny": "https://images.pexels.com/1-tiny.jpg",
            },
        }
    ]
}


@respx.mock
async def test_search_stock_images_uses_default_provider() -> None:
    respx.get("https://api.pexels.com/v1/search").mock(
        return_value=httpx.Response(200, json=_PEXELS_RESPONSE)
    )
    results = await server.search_stock_images("test query")
    assert len(results) == 1
    assert results[0].provider.value == "pexels"


@respx.mock
async def test_get_best_image_returns_top_result() -> None:
    respx.get("https://api.pexels.com/v1/search").mock(
        return_value=httpx.Response(200, json=_PEXELS_RESPONSE)
    )
    best = await server.get_best_image("test query")
    assert best is not None
    assert best.id == "1"


async def test_search_stock_images_rejects_unconfigured_provider() -> None:
    try:
        await server.search_stock_images("test query", provider="stockvault")
    except ValueError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("expected ValueError")


@respx.mock
async def test_search_then_get_attribution_round_trip() -> None:
    respx.get("https://api.pexels.com/v1/search").mock(
        return_value=httpx.Response(200, json=_PEXELS_RESPONSE)
    )
    results = await server.search_stock_images("test query")
    attribution = server.get_attribution("pexels", results[0].id)
    assert "Test Photographer" in attribution


def test_get_rate_limit_status_reports_all_providers() -> None:
    statuses = server.get_rate_limit_status()
    provider_names = {s.provider.value for s in statuses}
    assert provider_names == {"unsplash", "pexels", "pixabay", "freepik", "stockvault", "burst"}


async def test_search_all_images_skips_unconfigured_and_reports_string_reason() -> None:
    respx_router = respx.mock(assert_all_called=False)
    respx_router.get("https://api.pexels.com/v1/search").mock(
        return_value=httpx.Response(200, json=_PEXELS_RESPONSE)
    )
    respx_router.get(url__regex=r".*").mock(return_value=httpx.Response(500))
    with respx_router:
        output = await server.search_all_images("test query")

    assert isinstance(output["stockvault"], str)
    assert "not configured" in output["stockvault"]
