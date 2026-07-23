"""Burst by Shopify — UNOFFICIAL, best-effort HTML scraper.

Burst (burst.shopify.com) has no public API. This provider scrapes the public
search page's HTML instead. It is inherently fragile: any markup change on
Burst's site can silently break parsing, and scraping may run against
Burst/Shopify's terms of service. It requires no API key, uses a conservative
self-imposed rate limit (see config.burst_requests_per_minute), and every
failure is caught and surfaced as an empty result rather than raised, so it
never breaks search_all_images for the other, officially-supported providers.

Treat this provider as unsupported. Disable it by never calling it directly
and excluding "burst" from search_all_images if reliability matters.
"""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from stock_image_mcp.models import ImageResult, ProviderName, SearchParams
from stock_image_mcp.providers.base import ImageProvider

logger = logging.getLogger(__name__)


class BurstProvider(ImageProvider):
    name = ProviderName.BURST
    requires_api_key = False

    async def search(self, params: SearchParams) -> list[ImageResult]:
        try:
            response = await self.client.get(
                "https://burst.shopify.com/photos/search",
                params={"q": params.query},
            )
            response.raise_for_status()
            return self._parse(response.text)[: params.per_page]
        except Exception:
            logger.warning(
                "Burst scrape failed (unofficial/unsupported provider) for query=%r",
                params.query,
                exc_info=True,
            )
            return []

    def _parse(self, html: str) -> list[ImageResult]:
        soup = BeautifulSoup(html, "lxml")
        results: list[ImageResult] = []
        for card in soup.select("[data-photo-id]"):
            photo_id = card.get("data-photo-id")
            img = card.select_one("img")
            link = card.select_one("a")
            if not photo_id or img is None or link is None:
                continue
            raw_image_url = img.get("data-src") or img.get("src")
            raw_page_url = link.get("href")
            if not raw_image_url or not raw_page_url:
                continue
            image_url = str(raw_image_url)
            page_url = str(raw_page_url)
            if page_url.startswith("/"):
                page_url = f"https://burst.shopify.com{page_url}"
            alt_text = img.get("alt")
            results.append(
                ImageResult(
                    id=str(photo_id),
                    provider=self.name,
                    url=image_url,
                    thumbnail_url=image_url,
                    description=str(alt_text) if alt_text else None,
                    license="Burst License (unofficial scrape — verify manually)",
                    attribution_required=False,
                    source_page_url=page_url,
                )
            )
        return results

    def build_attribution(self, image: ImageResult) -> str:
        return (
            f"Image via Burst by Shopify ({image.source_page_url}) — "
            "sourced via unofficial scrape, verify license manually before use"
        )
