from __future__ import annotations

from stock_image_mcp.models import ImageResult, Orientation, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider

_ORIENTATION_MAP = {
    Orientation.LANDSCAPE: "horizontal",
    Orientation.PORTRAIT: "vertical",
    Orientation.SQUARE: "horizontal",  # Pixabay has no "square" option; default to horizontal
}


class PixabayProvider(ImageProvider):
    name = ProviderName.PIXABAY
    requires_api_key = True

    async def search(self, params: SearchParams) -> list[ImageResult]:
        query: dict[str, str | int] = {
            "key": self.api_key or "",
            "q": params.query,
            "image_type": "photo",
            "page": params.page,
            "per_page": max(params.per_page, 3),  # Pixabay requires per_page >= 3
        }
        if params.orientation is not None:
            query["orientation"] = _ORIENTATION_MAP[params.orientation]

        response = await self.client.get("https://pixabay.com/api/", params=query)
        response.raise_for_status()
        data = response.json()

        results: list[ImageResult] = []
        for item in data.get("hits", []):
            results.append(
                ImageResult(
                    id=str(item["id"]),
                    provider=self.name,
                    url=item["largeImageURL"],
                    thumbnail_url=item["previewURL"],
                    width=item.get("imageWidth"),
                    height=item.get("imageHeight"),
                    description=item.get("tags"),
                    photographer_name=item.get("user"),
                    photographer_url=(
                        f"https://pixabay.com/users/{item['user']}-{item['user_id']}/"
                        if item.get("user") and item.get("user_id")
                        else None
                    ),
                    license="Pixabay License",
                    attribution_required=False,
                    source_page_url=item["pageURL"],
                )
            )
        return results

    def build_attribution(self, image: ImageResult) -> str:
        name = image.photographer_name or "Unknown"
        return (
            f"Image by {name} from Pixabay ({image.source_page_url}) — "
            "attribution appreciated but not required by license"
        )
