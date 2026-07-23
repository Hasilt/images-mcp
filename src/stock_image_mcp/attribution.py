"""Thin wrapper for formatting attribution text for a given image."""

from __future__ import annotations

from stock_image_mcp.models import ImageResult, ProviderName
from stock_image_mcp.providers.base import ImageProvider


def format_attribution(image: ImageResult, providers: dict[ProviderName, ImageProvider]) -> str:
    provider = providers[image.provider]
    return provider.build_attribution(image)
