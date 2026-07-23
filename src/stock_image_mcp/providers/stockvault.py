"""StockVault provider.

StockVault's API docs (stockvault.net/api) describe keyword search with
pagination and JSON/XML output; the exact response schema is not fully
published. Field mapping here is a best-effort, reasonable guess — verify
against a live response before relying on this in production.
"""

from __future__ import annotations

from stock_image_mcp.models import ImageResult, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider


class StockVaultProvider(ImageProvider):
    name = ProviderName.STOCKVAULT
    requires_api_key = True

    async def search(self, params: SearchParams) -> list[ImageResult]:
        query: dict[str, str | int] = {
            "key": self.api_key or "",
            "q": params.query,
            "page": params.page,
            "per_page": params.per_page,
            "format": "json",
        }

        response = await self.client.get("https://www.stockvault.net/api/search", params=query)
        response.raise_for_status()
        data = response.json()

        results: list[ImageResult] = []
        for item in data.get("results", []):
            results.append(
                ImageResult(
                    id=str(item["id"]),
                    provider=self.name,
                    url=item["image_url"],
                    thumbnail_url=item.get("thumbnail_url", item["image_url"]),
                    width=item.get("width"),
                    height=item.get("height"),
                    description=item.get("title"),
                    photographer_name=item.get("author"),
                    photographer_url=item.get("author_url"),
                    license="StockVault License",
                    attribution_required=True,
                    source_page_url=item.get("page_url", item["image_url"]),
                )
            )
        return results

    def build_attribution(self, image: ImageResult) -> str:
        name = image.photographer_name or "Unknown"
        return f"Image by {name} via StockVault ({image.source_page_url})"
