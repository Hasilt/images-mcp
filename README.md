# stock-image-mcp

<!-- mcp-name: io.github.Hasilt/images-mcp -->

An MCP server that lets Claude Code (or any MCP-compatible agent) search and
download stock images by tool call — useful for sourcing images while writing
SEO blog posts or other content.

## Providers

| Provider | API type | Requires key | Default rate limit |
|---|---|---|---|
| Unsplash | Official | Yes | 50/hr demo, 5000/hr production |
| Pexels | Official | Yes | 200/hr |
| Pixabay | Official | Yes | 100 req/60s |
| Freepik | Official | Yes | configurable (plan-dependent) |
| StockVault | Official | Yes | configurable (undocumented, conservative default) |
| Burst (Shopify) | **Unofficial scrape** | No | self-imposed, polite default |

Burst has no public API. It's included as a best-effort HTML scraper, clearly
marked unsupported in code — any failure there is caught and reported as an
empty result rather than breaking `search_all_images`.

## Install

Each user runs the server locally and supplies their own provider API keys —
there's no shared hosting or centrally-held keys.

Add it to your Claude config with [`uvx`](https://docs.astral.sh/uv/guides/tools/)
(no clone or install step required — `uvx` fetches the package from PyPI on
first run):

```json
{
  "mcpServers": {
    "stock-image-mcp": {
      "command": "uvx",
      "args": ["stock-image-mcp"],
      "env": {
        "PEXELS_API_KEY": "...",
        "UNSPLASH_ACCESS_KEY": "..."
      }
    }
  }
}
```

Any provider env var you omit is simply skipped by `search_all_images` and
rejected if queried directly via `search_stock_images` — see `.env.example`
for the full list of supported keys.

## Tools

- `search_stock_images(query, provider="default", orientation=None, per_page=10, page=1)`
- `search_all_images(query, orientation=None, per_page=5)` — fans out to every configured provider concurrently
- `get_best_image(query, provider="default")`
- `download_image(url, dest_path, provider=None)` — saves locally, returns attribution text if the image came from a prior search
- `get_attribution(provider, image_id)`
- `get_rate_limit_status(provider=None)`

## Developing locally

Working from a clone instead of the published package:

```bash
uv sync
cp .env.example .env   # fill in the API keys for providers you want enabled
uv run stock-image-mcp
```

Point your Claude config at the local checkout instead of `uvx`:

```json
{
  "mcpServers": {
    "stock-image-mcp": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/stock-image-mcp", "run", "stock-image-mcp"],
      "env": {
        "PEXELS_API_KEY": "...",
        "UNSPLASH_ACCESS_KEY": "..."
      }
    }
  }
}
```

## Development

```bash
uv run pytest              # test suite (mocked HTTP, no live keys needed)
uv run ruff check .         # lint
uv run ruff format .        # format
uv run mypy src             # type check
```

To try it against real providers, use the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector):

```bash
npx @modelcontextprotocol/inspector uv run stock-image-mcp
```

## Releasing

Publishing to PyPI is handled by `.github/workflows/publish.yml`, triggered by
pushing a `v*` tag (e.g. `v0.1.0`). It runs lint/type-check/tests, builds the
package, then publishes via PyPI's trusted-publisher (OIDC) flow — no token
stored in CI.

One-time setup on PyPI (before the first tagged release): add a "pending
publisher" at <https://pypi.org/manage/account/publishing/> with PyPI project
name `stock-image-mcp`, repo owner `Hasilt`, repo name `images-mcp`, workflow
filename `publish.yml`, and environment `pypi`. PyPI creates the project
automatically on the first successful run of that workflow.
