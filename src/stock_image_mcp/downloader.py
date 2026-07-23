"""Downloads an image to a local path for direct embedding in blog output."""

from __future__ import annotations

from pathlib import Path

import httpx


async def download_image(client: httpx.AsyncClient, url: str, dest_path: Path) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    async with client.stream("GET", url) as response:
        response.raise_for_status()
        with dest_path.open("wb") as f:
            async for chunk in response.aiter_bytes():
                f.write(chunk)
    return dest_path
