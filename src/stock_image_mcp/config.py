"""Environment-driven configuration for the server and its providers."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from stock_image_mcp.models import ProviderName


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    unsplash_access_key: str | None = None
    unsplash_tier: str = "demo"  # "demo" (50/hr) or "production" (5000/hr)

    pexels_api_key: str | None = None

    pixabay_api_key: str | None = None

    freepik_api_key: str | None = None
    freepik_requests_per_minute: int = 60

    stockvault_api_key: str | None = None
    stockvault_requests_per_hour: int = 60

    burst_requests_per_minute: int = 10  # self-imposed, polite default (no official API)

    default_provider: ProviderName = ProviderName.PEXELS
    download_dir: Path = Path("./downloads")

    def api_key_for(self, provider: ProviderName) -> str | None:
        return {
            ProviderName.UNSPLASH: self.unsplash_access_key,
            ProviderName.PEXELS: self.pexels_api_key,
            ProviderName.PIXABAY: self.pixabay_api_key,
            ProviderName.FREEPIK: self.freepik_api_key,
            ProviderName.STOCKVAULT: self.stockvault_api_key,
            ProviderName.BURST: "unofficial",  # no key required/possible
        }[provider]

    def is_configured(self, provider: ProviderName) -> bool:
        return self.api_key_for(provider) is not None


def get_settings() -> Settings:
    return Settings()
