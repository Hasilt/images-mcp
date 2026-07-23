from __future__ import annotations

from pathlib import Path

import httpx
import respx

from stock_image_mcp.downloader import download_image


@respx.mock
async def test_download_image_saves_bytes(tmp_path: Path) -> None:
    respx.get("https://example.com/photo.jpg").mock(
        return_value=httpx.Response(200, content=b"fake-image-bytes")
    )
    dest = tmp_path / "nested" / "photo.jpg"

    async with httpx.AsyncClient() as client:
        saved_path = await download_image(client, "https://example.com/photo.jpg", dest)

    assert saved_path == dest
    assert dest.read_bytes() == b"fake-image-bytes"


@respx.mock
async def test_download_image_raises_on_http_error(tmp_path: Path) -> None:
    respx.get("https://example.com/missing.jpg").mock(return_value=httpx.Response(404))
    dest = tmp_path / "missing.jpg"

    async with httpx.AsyncClient() as client:
        try:
            await download_image(client, "https://example.com/missing.jpg", dest)
        except httpx.HTTPStatusError:
            pass
        else:
            raise AssertionError("expected HTTPStatusError")

    assert not dest.exists()
