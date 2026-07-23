from __future__ import annotations

import httpx

from stock_image_mcp.config import Settings
from stock_image_mcp.models import ProviderName
from stock_image_mcp.providers.base import ImageProvider
from stock_image_mcp.providers.burst import BurstProvider
from stock_image_mcp.providers.freepik import FreepikProvider
from stock_image_mcp.providers.pexels import PexelsProvider
from stock_image_mcp.providers.pixabay import PixabayProvider
from stock_image_mcp.providers.stockvault import StockVaultProvider
from stock_image_mcp.providers.unsplash import UnsplashProvider

__all__ = [
    "BurstProvider",
    "FreepikProvider",
    "PexelsProvider",
    "PixabayProvider",
    "StockVaultProvider",
    "UnsplashProvider",
    "build_providers",
]

_PROVIDER_CLASSES: dict[ProviderName, type[ImageProvider]] = {
    ProviderName.UNSPLASH: UnsplashProvider,
    ProviderName.PEXELS: PexelsProvider,
    ProviderName.PIXABAY: PixabayProvider,
    ProviderName.FREEPIK: FreepikProvider,
    ProviderName.STOCKVAULT: StockVaultProvider,
    ProviderName.BURST: BurstProvider,
}


def build_providers(
    settings: Settings, client: httpx.AsyncClient
) -> dict[ProviderName, ImageProvider]:
    return {
        name: cls(settings.api_key_for(name), client) for name, cls in _PROVIDER_CLASSES.items()
    }
