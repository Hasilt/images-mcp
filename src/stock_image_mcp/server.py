"""MCP server exposing stock image search/download tools to LLM agents."""

from __future__ import annotations

from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

from stock_image_mcp.aggregator import search_all
from stock_image_mcp.attribution import format_attribution
from stock_image_mcp.config import Settings, get_settings
from stock_image_mcp.downloader import download_image as _download_image
from stock_image_mcp.models import (
    ImageResult,
    Orientation,
    ProviderName,
    RateLimitStatus,
    SearchParams,
)
from stock_image_mcp.providers import build_providers
from stock_image_mcp.providers.base import ImageProvider
from stock_image_mcp.rate_limiter import RateLimiter

mcp = FastMCP("stock-image-mcp")

_settings: Settings = get_settings()
_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
_providers: dict[ProviderName, ImageProvider] = build_providers(_settings, _client)
_RATE_LIMIT_CONFIG: dict[ProviderName, tuple[int, int]] = {
    ProviderName.UNSPLASH: (5000 if _settings.unsplash_tier == "production" else 50, 3600),
    ProviderName.PEXELS: (200, 3600),
    ProviderName.PIXABAY: (100, 60),
    ProviderName.FREEPIK: (_settings.freepik_requests_per_minute, 60),
    ProviderName.STOCKVAULT: (_settings.stockvault_requests_per_hour, 3600),
    ProviderName.BURST: (_settings.burst_requests_per_minute, 60),
}

_rate_limiter = RateLimiter()
for _name, (_limit, _window) in _RATE_LIMIT_CONFIG.items():
    _rate_limiter.configure(_name, _limit, _window)

# Cache of recently seen results, so get_attribution/download_image can resolve
# an id previously returned by a search call without re-querying the provider.
_result_cache: dict[tuple[ProviderName, str], ImageResult] = {}


def _cache_results(results: list[ImageResult]) -> None:
    for result in results:
        _result_cache[(result.provider, result.id)] = result


def _resolve_provider(provider: str) -> ProviderName:
    if provider == "default":
        return _settings.default_provider
    return ProviderName(provider)


@mcp.tool()
async def search_stock_images(
    query: str,
    provider: str = "default",
    orientation: str | None = None,
    per_page: int = 10,
    page: int = 1,
) -> list[ImageResult]:
    """Search a single stock image provider (or the configured default) for a query."""
    provider_name = _resolve_provider(provider)
    image_provider = _providers[provider_name]
    if not image_provider.configured:
        raise ValueError(f"{provider_name} is not configured (missing API key)")

    params = SearchParams(
        query=query,
        orientation=Orientation(orientation) if orientation else None,
        per_page=per_page,
        page=page,
    )
    await _rate_limiter.acquire(provider_name)
    results = await image_provider.search(params)
    _cache_results(results)
    return results


@mcp.tool()
async def search_all_images(
    query: str, orientation: str | None = None, per_page: int = 5
) -> dict[str, list[ImageResult] | str]:
    """Search every configured provider concurrently; unconfigured or rate-limited
    providers are skipped with a note rather than failing the whole call."""
    params = SearchParams(
        query=query,
        orientation=Orientation(orientation) if orientation else None,
        per_page=per_page,
    )
    outcomes = await search_all(_providers, params, _rate_limiter)
    output: dict[str, list[ImageResult] | str] = {}
    for provider_name, outcome in outcomes.items():
        _cache_results(outcome.results)
        output[provider_name.value] = outcome.skipped_reason or outcome.results
    return output


@mcp.tool()
async def get_best_image(query: str, provider: str = "default") -> ImageResult | None:
    """Return the single top-ranked result for a query from one provider."""
    results = await search_stock_images(query, provider=provider, per_page=1, page=1)
    return results[0] if results else None


@mcp.tool()
async def download_image(url: str, dest_path: str, provider: str | None = None) -> dict[str, str]:
    """Download an image URL to a local path so it can be embedded directly
    in a blog post's asset folder. Returns the saved path and, if the image
    was previously returned by a search call, its attribution text."""
    path = Path(dest_path)
    if not path.is_absolute():
        path = _settings.download_dir / path
    saved_path = await _download_image(_client, url, path)

    attribution_text = None
    if provider is not None:
        provider_name = _resolve_provider(provider)
        cached = next(
            (img for (p, _), img in _result_cache.items() if p == provider_name and img.url == url),
            None,
        )
        if cached is not None:
            attribution_text = format_attribution(cached, _providers)

    return {
        "saved_path": str(saved_path),
        "attribution": attribution_text or "unknown (image was not looked up from a prior search)",
    }


@mcp.tool()
def get_attribution(provider: str, image_id: str) -> str:
    """Return formatted credit/attribution text for a previously-returned image."""
    provider_name = _resolve_provider(provider)
    cached = _result_cache.get((provider_name, image_id))
    if cached is None:
        raise ValueError(
            f"No cached result for {provider_name}:{image_id}; call search_stock_images first"
        )
    return format_attribution(cached, _providers)


@mcp.tool()
def get_rate_limit_status(provider: str | None = None) -> list[RateLimitStatus]:
    """Inspect remaining request quota per provider before deciding where to search."""
    names = [_resolve_provider(provider)] if provider else list(_providers)
    statuses = []
    for name in names:
        limit, window = _RATE_LIMIT_CONFIG[name]
        statuses.append(
            RateLimitStatus(
                provider=name,
                limit=limit,
                window_seconds=window,
                remaining=_rate_limiter.remaining(name),
                configured=_providers[name].configured,
            )
        )
    return statuses


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
