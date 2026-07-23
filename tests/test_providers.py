from __future__ import annotations

import httpx
import pytest
import respx

from stock_image_mcp.models import Orientation, SearchParams
from stock_image_mcp.providers.burst import BurstProvider
from stock_image_mcp.providers.freepik import FreepikProvider
from stock_image_mcp.providers.pexels import PexelsProvider
from stock_image_mcp.providers.pixabay import PixabayProvider
from stock_image_mcp.providers.stockvault import StockVaultProvider
from stock_image_mcp.providers.unsplash import UnsplashProvider


@pytest.fixture
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient() as c:
        yield c


class TestUnsplash:
    @respx.mock
    async def test_search_parses_results(self, client: httpx.AsyncClient) -> None:
        respx.get("https://api.unsplash.com/search/photos").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "abc123",
                            "description": "A mountain",
                            "alt_description": None,
                            "width": 4000,
                            "height": 3000,
                            "urls": {
                                "full": "https://images.unsplash.com/abc123-full",
                                "thumb": "https://images.unsplash.com/abc123-thumb",
                            },
                            "user": {
                                "name": "Jane Doe",
                                "links": {"html": "https://unsplash.com/@jane"},
                            },
                            "links": {"html": "https://unsplash.com/photos/abc123"},
                        }
                    ]
                },
            )
        )
        provider = UnsplashProvider("fake-key", client)
        results = await provider.search(SearchParams(query="mountain"))

        assert len(results) == 1
        result = results[0]
        assert result.id == "abc123"
        assert result.photographer_name == "Jane Doe"
        assert result.attribution_required is False
        assert "Photo by Jane Doe" in provider.build_attribution(result)

    def test_configured_requires_key(
        self,
    ) -> None:
        assert UnsplashProvider(None, httpx.AsyncClient()).configured is False
        assert UnsplashProvider("key", httpx.AsyncClient()).configured is True


class TestPexels:
    @respx.mock
    async def test_search_parses_results(self, client: httpx.AsyncClient) -> None:
        respx.get("https://api.pexels.com/v1/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "photos": [
                        {
                            "id": 42,
                            "width": 1920,
                            "height": 1080,
                            "url": "https://www.pexels.com/photo/42",
                            "photographer": "John Smith",
                            "photographer_url": "https://www.pexels.com/@john",
                            "alt": "A desk",
                            "src": {
                                "original": "https://images.pexels.com/42-original.jpg",
                                "tiny": "https://images.pexels.com/42-tiny.jpg",
                            },
                        }
                    ]
                },
            )
        )
        provider = PexelsProvider("fake-key", client)
        results = await provider.search(
            SearchParams(query="desk", orientation=Orientation.LANDSCAPE)
        )

        assert len(results) == 1
        assert results[0].id == "42"
        assert results[0].photographer_name == "John Smith"


class TestPixabay:
    @respx.mock
    async def test_search_parses_results(self, client: httpx.AsyncClient) -> None:
        respx.get("https://pixabay.com/api/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "hits": [
                        {
                            "id": 7,
                            "pageURL": "https://pixabay.com/photos/7",
                            "tags": "forest, trees",
                            "previewURL": "https://cdn.pixabay.com/7-preview.jpg",
                            "largeImageURL": "https://cdn.pixabay.com/7-large.jpg",
                            "user": "artist99",
                            "user_id": 555,
                            "imageWidth": 1280,
                            "imageHeight": 720,
                        }
                    ]
                },
            )
        )
        provider = PixabayProvider("fake-key", client)
        results = await provider.search(SearchParams(query="forest"))

        assert len(results) == 1
        assert results[0].photographer_name == "artist99"
        assert "pixabay.com/users/artist99-555" in str(results[0].photographer_url)


class TestFreepik:
    @respx.mock
    async def test_search_parses_results(self, client: httpx.AsyncClient) -> None:
        respx.get("https://api.freepik.com/v1/resources").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 99,
                            "title": "Office space",
                            "url": "https://freepik.com/photo/99",
                            "image": {
                                "source": {"url": "https://cdn.freepik.com/99.jpg"},
                                "thumbnail": {"url": "https://cdn.freepik.com/99-thumb.jpg"},
                            },
                            "author": {"name": "Studio X"},
                            "licenses": [{"type": "freemium"}],
                        }
                    ]
                },
            )
        )
        provider = FreepikProvider("fake-key", client)
        results = await provider.search(SearchParams(query="office"))

        assert len(results) == 1
        assert results[0].attribution_required is True
        assert "Studio X" in provider.build_attribution(results[0])


class TestStockVault:
    @respx.mock
    async def test_search_parses_results(self, client: httpx.AsyncClient) -> None:
        respx.get("https://www.stockvault.net/api/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "sv1",
                            "title": "Texture",
                            "image_url": "https://stockvault.net/sv1.jpg",
                            "thumbnail_url": "https://stockvault.net/sv1-thumb.jpg",
                            "author": "Alice",
                            "page_url": "https://stockvault.net/photo/sv1",
                        }
                    ]
                },
            )
        )
        provider = StockVaultProvider("fake-key", client)
        results = await provider.search(SearchParams(query="texture"))

        assert len(results) == 1
        assert results[0].photographer_name == "Alice"


class TestBurst:
    def test_no_api_key_required(self) -> None:
        assert BurstProvider(None, httpx.AsyncClient()).configured is True

    @respx.mock
    async def test_search_parses_html(self, client: httpx.AsyncClient) -> None:
        html = """
        <div data-photo-id="55">
            <a href="/photos/55-cool-shot">
                <img src="https://burst.shopifycdn.com/55.jpg" alt="Cool shot" />
            </a>
        </div>
        """
        respx.get("https://burst.shopify.com/photos/search").mock(
            return_value=httpx.Response(200, text=html)
        )
        provider = BurstProvider(None, client)
        results = await provider.search(SearchParams(query="cool"))

        assert len(results) == 1
        assert results[0].id == "55"
        assert str(results[0].source_page_url) == "https://burst.shopify.com/photos/55-cool-shot"

    @respx.mock
    async def test_search_failure_returns_empty_not_raises(self, client: httpx.AsyncClient) -> None:
        respx.get("https://burst.shopify.com/photos/search").mock(return_value=httpx.Response(500))
        provider = BurstProvider(None, client)
        results = await provider.search(SearchParams(query="cool"))
        assert results == []
