from __future__ import annotations

from stock_image_mcp.models import ImageResult, Orientation, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider

_ORIENTATION_MAP = {
    Orientation.LANDSCAPE: "landscape",
    Orientation.PORTRAIT: "portrait",
    Orientation.SQUARE: "squarish",
}


class UnsplashProvider(ImageProvider):
    name = ProviderName.UNSPLASH
    requires_api_key = True

    async def search(self, params: SearchParams) -> list[ImageResult]:
        query: dict[str, str | int] = {
            "query": params.query,
            "page": params.page,
            "per_page": params.per_page,
        }
        if params.orientation is not None:
            query["orientation"] = _ORIENTATION_MAP[params.orientation]

        response = await self.client.get(
            "https://api.unsplash.com/search/photos",
            params=query,
            headers={"Authorization": f"Client-ID {self.api_key}"},
        )
        response.raise_for_status()
        data = response.json()

        results: list[ImageResult] = []
        for item in data.get("results", []):
            user = item.get("user") or {}
            results.append(
                ImageResult(
                    id=str(item["id"]),
                    provider=self.name,
                    url=item["urls"]["full"],
                    thumbnail_url=item["urls"]["thumb"],
                    width=item.get("width"),
                    height=item.get("height"),
                    description=item.get("description") or item.get("alt_description"),
                    photographer_name=user.get("name"),
                    photographer_url=(user.get("links") or {}).get("html"),
                    license="Unsplash License",
                    attribution_required=False,
                    source_page_url=(item.get("links") or {}).get("html", item["urls"]["full"]),
                )
            )
        return results

    def build_attribution(self, image: ImageResult) -> str:
        name = image.photographer_name or "Unknown"
        return (
            f"Photo by {name} on Unsplash ({image.source_page_url}) — "
            "attribution appreciated but not required by license"
        )
