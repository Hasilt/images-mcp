from __future__ import annotations

from stock_image_mcp.models import ImageResult, Orientation, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider

_ORIENTATION_MAP = {
    Orientation.LANDSCAPE: "landscape",
    Orientation.PORTRAIT: "portrait",
    Orientation.SQUARE: "square",
}


class PexelsProvider(ImageProvider):
    name = ProviderName.PEXELS
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
            "https://api.pexels.com/v1/search",
            params=query,
            headers={"Authorization": self.api_key or ""},
        )
        response.raise_for_status()
        data = response.json()

        results: list[ImageResult] = []
        for item in data.get("photos", []):
            src = item.get("src", {})
            results.append(
                ImageResult(
                    id=str(item["id"]),
                    provider=self.name,
                    url=src.get("original", src.get("large")),
                    thumbnail_url=src.get("tiny", src.get("small")),
                    width=item.get("width"),
                    height=item.get("height"),
                    description=item.get("alt") or None,
                    photographer_name=item.get("photographer"),
                    photographer_url=item.get("photographer_url"),
                    license="Pexels License",
                    attribution_required=False,
                    source_page_url=item.get("url", src.get("original")),
                )
            )
        return results

    def build_attribution(self, image: ImageResult) -> str:
        name = image.photographer_name or "Unknown"
        return (
            f"Photo by {name} on Pexels ({image.source_page_url}) — "
            "attribution appreciated but not required by license"
        )
