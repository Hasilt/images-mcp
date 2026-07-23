"""Abstract interface every image provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from stock_image_mcp.models import ImageResult, ProviderName, SearchParams


class ImageProvider(ABC):
    name: ProviderName
    requires_api_key: bool = True

    def __init__(self, api_key: str | None, client: httpx.AsyncClient) -> None:
        self.api_key = api_key
        self.client = client

    @property
    def configured(self) -> bool:
        return not self.requires_api_key or self.api_key is not None

    @abstractmethod
    async def search(self, params: SearchParams) -> list[ImageResult]: ...

    @abstractmethod
    def build_attribution(self, image: ImageResult) -> str: ...
