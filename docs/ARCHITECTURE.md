# Architecture

## Overview

gitee-mcp bridges MCP hosts (Claude Desktop, Cursor, opencode) and a webapp
to the Gitee v5 API. It has two honest access tiers:

| Tier | Requires | Surface |
|------|----------|---------|
| **Anonymous** | nothing | repo details, README, languages, commits, branches, contents, user search, user repos, humming radar. Rate-limited to ~60 req/hour |
| **Token** | free GITEE_TOKEN | + repo search, top-starred/top-forked, stargazers, radar search-mixing |

Gitee endpoints that are NOT available are documented in the client
(`src/gitee_mcp/client.py`): the explore/trending pages answer HTTP 405 to
non-browser clients (anti-bot challenge), and anonymous repo search returns
an empty array. The server never fabricates either surface.

## Components

```
webapp (React, :11162) ─┐
                        ├──► FastAPI (:11161)
MCP clients (stdio/HTTP)┘      │  ├── /mcp        FastMCP streamable HTTP (lifespan-chained)
                               │  ├── /api/*      REST (same tool functions as MCP)
                               │  ├── /docs       Swagger UI
                               ▼
                        gitee_mcp.tools.* (portmanteaus, shared with MCP)
                               ▼
                        GiteeClient (httpx) ──► gitee.com/api/v5
                               │  └── JsonCache (data/cache, TTL 600s)
                        Translator ──► Ollama :11434 (zh->en, gloss fallback)
                        WebhookReceiver (data/webhook_events.jsonl)
```

Both the webapp and the MCP surface call the **same** tool functions
(`gitee_repo`, `gitee_search`, ...), so the browser and Claude can never
disagree about behavior.

## Dual transport

- **stdio** (default): `uv run python -m gitee_mcp.server`
- **HTTP**: `uv run python -m gitee_mcp.server --mode http --port 11161`, or
  set `MCP_PORT`/`PORT` and run `run_server.py` (PyInstaller/MCPB entry).

The FastAPI app owns the MCP app's lifespan (FastMCP 3.4.4 pattern):

```python
_mcp_http = mcp.http_app(path="/")
app = FastAPI(..., lifespan=_mcp_http.lifespan)
app.mount("/mcp", _mcp_http)
```

## The humming radar

Gitee has no public trending API, so the radar computes its own ranking
from live data:

1. Seed repos (curated defaults or `GITEE_SEED_REPOS`)
2. Live `repo details` + 10 most recent `commits` per seed (cached 10 min)
3. `activity_score = commit recency (decayed, up to 2.0 each) + commit
   volume (1.5 each) + stars (up to 3.0) + forks (up to 1.5)`
4. Dead seeds (404) are dropped and reported in `dead_seeds`
5. Token tier additionally mixes in top-starred search results

Methodology lives in `src/gitee_mcp/radar.py`; the score is exposed in
every response so agents can verify the ranking.

## Translation

- Probe `GET {base}/models` (default Ollama on 11434)
- `POST {base}/chat/completions` with temperature 0.2
- Provider down -> built-in Chinese OSS glossary + `translated: false`
  (never a fabricated translation)

## Caching and rate limits

- `JsonCache` under `data/cache`, TTL `GITEE_CACHE_TTL` (600s default)
- `X-RateLimit-Remaining` is tracked and surfaced in
  `/api/health` and `show_gitee_status_card`

## Webhooks

- `POST /api/webhooks/gitee` verifies `X-Gitee-Token` against
  `GITEE_WEBHOOK_SECRET` (when set), appends to
  `data/webhook_events.jsonl`
- `gitee_webhook(operation=list|clear)` + webapp Inbox read the feed

## Ports

Registered in `mcp-central-docs/operations/WEBAPP_PORTS.md`:

| Port | Service |
|------|---------|
| 11161 | gitee-mcp backend (REST + MCP) |
| 11162 | gitee-mcp frontend (Vite) |

## Security

- No secrets in code; `.env` is gitignored; `.env.example` ships instead
- CORS: explicit localhost/Tauri origins + LAN/Tailscale regex - no `*`
- Webhook secret checked at the receiver
- LLM traffic is localhost-only by default (Ollama), no cloud keys needed
