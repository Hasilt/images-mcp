# stock-image-mcp

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

## Setup

```bash
uv sync
cp .env.example .env   # fill in the API keys for providers you want enabled
```

## Tools

- `search_images(query, provider="default", orientation=None, per_page=10, page=1)`
- `search_all_images(query, orientation=None, per_page=5)` — fans out to every configured provider concurrently
- `get_best_image(query, provider="default")`
- `download_image(url, dest_path, provider=None)` — saves locally, returns attribution text if the image came from a prior search
- `get_attribution(provider, image_id)`
- `get_rate_limit_status(provider=None)`

## Running

```bash
uv run stock-image-mcp
```

### Registering with Claude Code

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
