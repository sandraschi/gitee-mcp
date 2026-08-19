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

                        Ecosystem layer (v0.2) - local persistence under data/
                        history.py     radar snapshots -> momentum/star series (data/radar_history.jsonl)
                        watchlist.py   persistent watchlist + change detection (data/watchlist.json)
                        corpus.py      README BM25 index, SQLite FTS5 (data/corpus.db)
                        ecosystem.py   graph / mirror / weekly digest (data/digest-latest.md)
                        feed.py        RSS 2.0 radar feed
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

## Ecosystem intelligence (v0.2)

The radar answers "what is humming now"; the ecosystem layer answers
"what is changing". All of it is derived from real API calls or locally
persisted observations - nothing is fabricated.

| Module | Purpose | Storage |
|--------|---------|---------|
| `history.py` | Snapshot every radar build; compute `momentum` / `momentum_7d` / `surge`, observed star/forks series, and top movers for the digest | `data/radar_history.jsonl` (capped 2000 rows) |
| `watchlist.py` | Persistent watchlist with commit-hash change detection + optional `min_activity` auto-follow thresholds | `data/watchlist.json` |
| `stack.py` | Chinese-OSS tech-stack fingerprint (RuoYi, Spring Boot/Cloud, MyBatis-Plus, Vue2/3, TDesign, Go, ...) from README + contents | cached 10 min |
| `release_notes.py` | Latest Gitee releases + English summary (LLM, glossary fallback) | cached 10 min |
| `ecosystem.py` | Org/fork-family graph, GitHub mirror comparison (cached 1h), weekly "who's rising" digest | `data/digest-latest.md` |
| `corpus.py` | README BM25 keyword index (SQLite FTS5, RAG-lite); READMEs auto-index on `gitee_repo(readme)` | `data/corpus.db` |
| `feed.py` | RSS 2.0 radar feed (`GET /api/feed.xml`) | regenerated per request |
| `search_expand.py` | Cross-lingual repo-search query expansion (EN->ZH synonym map) | static |

Honesty rules enforced across the layer: momentum is `null` on the first
observation (no fabricated 0); star-history and the digest are labeled as
*gitee-mcp observations*, not Gitee's full history; the GitHub mirror
returns "not found" for Gitee-only projects; the corpus is explicitly BM25
keyword retrieval, not embeddings. The full feature spec lives in
`SPEC.md`.

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
- `gitee_webhook(operation=list|clear|digest)` + webapp Inbox read the
  feed; `digest` groups events by repo into a daily-style report

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
