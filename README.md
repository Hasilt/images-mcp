# stock-image-mcp

<!-- mcp-name: io.github.Hasilt/images-mcp -->

An MCP server that lets Claude Code (or any MCP-compatible agent) search and
download stock images by tool call — useful for sourcing images while writing
SEO blog posts or other content.

## Providers

| Provider        | API type              | Requires key | Default rate limit                                |
| --------------- | --------------------- | ------------ | ------------------------------------------------- |
| Unsplash        | Official              | Yes          | 50/hr demo, 5000/hr production                    |
| Pexels          | Official              | Yes          | 200/hr                                            |
| Pixabay         | Official              | Yes          | 100 req/60s                                       |
| Freepik         | Official              | Yes          | configurable (plan-dependent)                     |
| StockVault      | Official              | Yes          | configurable (undocumented, conservative default) |
| Burst (Shopify) | **Unofficial scrape** | No           | self-imposed, polite default                      |

Burst has no public API. It's included as a best-effort HTML scraper, clearly
marked unsupported in code — any failure there is caught and reported as an
empty result rather than breaking `search_all_images`.

## Install

Each user runs the server locally and supplies their own provider API keys —
there's no shared hosting or centrally-held keys.

With [Claude Code](https://docs.claude.com/en/docs/claude-code):

```bash
claude mcp add stock-image-mcp -e PEXELS_API_KEY=... -e UNSPLASH_ACCESS_KEY=... -- uvx stock-image-mcp
```

With [OpenAI Codex CLI](https://github.com/openai/codex):

```bash
codex mcp add stock-image-mcp --env PEXELS_API_KEY=... --env UNSPLASH_ACCESS_KEY=... -- uvx stock-image-mcp
```

With [Gemini CLI](https://github.com/google-gemini/gemini-cli):

```bash
gemini mcp add stock-image-mcp -e PEXELS_API_KEY=... -e UNSPLASH_ACCESS_KEY=... -- uvx stock-image-mcp
```

Or add it to your MCP config manually with [`uvx`](https://docs.astral.sh/uv/guides/tools/)
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

## Usage

You don't call these tools directly — you just talk to your agent, and it
decides when to reach for one based on what you asked and the tool
descriptions above. A few things worth knowing:

- Just ask in plain English. "Find me 3 landscape photos of mountains for a
  blog post" is enough to trigger `search_all_images` (or
  `search_stock_images` if you name a provider). "Download that first
  Unsplash result to `./images/hero.jpg`" triggers `download_image`. "How
  many Pexels requests do I have left this hour?" triggers
  `get_rate_limit_status`.
- `search_stock_images` needs a specific provider (or `"default"`);
  `search_all_images` just queries everything you've configured keys for and
  merges the results. Say "search Pexels only" or similar if you care which
  one gets used.
- Several providers (Unsplash and Pexels in particular) require attribution
  if you actually use the image somewhere public. `download_image` returns
  the attribution text alongside the file when it applies — it's on you to
  paste it wherever the image ends up, the server won't do that part for you.
- Want to call tools by hand instead of through a conversation? See the MCP
  Inspector section under Development below.

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
      "args": [
        "--directory",
        "/absolute/path/to/stock-image-mcp",
        "run",
        "stock-image-mcp"
      ],
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
