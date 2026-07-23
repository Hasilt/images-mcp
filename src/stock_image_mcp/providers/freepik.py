"""Freepik stock content provider.

Field mapping is based on the documented /v1/resources schema
(https://docs.freepik.com/api-reference/resources/stock-content) as of writing.
Freepik's API evolves independently of this project — verify field names against
a live response before relying on this in production.
"""

from __future__ import annotations

from stock_image_mcp.models import ImageResult, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider


class FreepikProvider(ImageProvider):
    name = ProviderName.FREEPIK
    requires_api_key = True

    async def search(self, params: SearchParams) -> list[ImageResult]:
        query: dict[str, str | int] = {
            "term": params.query,
            "limit": params.per_page,
            "page": params.page,
            "filters[content_type]": "photo",
        }
        if params.orientation is not None:
            query[f"filters[orientation][{params.orientation.value}]"] = 1

        response = await self.client.get(
            "https://api.freepik.com/v1/resources",
            params=query,
            headers={"x-freepik-api-key": self.api_key or ""},
        )
        response.raise_for_status()
        data = response.json()

        results: list[ImageResult] = []
        for item in data.get("data", []):
            image = item.get("image") or {}
            source = image.get("source") or {}
            author = item.get("author") or {}
            licenses = item.get("licenses") or []
            is_premium = any(lic.get("type") == "premium" for lic in licenses)
            source_url = str(source["url"])
            results.append(
                ImageResult(
                    id=str(item["id"]),
                    provider=self.name,
                    url=source_url,
                    thumbnail_url=str((image.get("thumbnail") or {}).get("url", source_url)),
                    width=source.get("size", {}).get("width") if source.get("size") else None,
                    height=source.get("size", {}).get("height") if source.get("size") else None,
                    description=item.get("title"),
                    photographer_name=author.get("name"),
                    photographer_url=author.get("avatar"),
                    license="Freepik Premium" if is_premium else "Freepik Freemium",
                    attribution_required=not is_premium,
                    source_page_url=str(item.get("url", source_url)),
                )
            )
        return results

    def build_attribution(self, image: ImageResult) -> str:
        if not image.attribution_required:
            return f"Freepik Premium image ({image.source_page_url}) — no attribution required"
        name = image.photographer_name or "Freepik"
        return f"Image by {name} on Freepik ({image.source_page_url})"
