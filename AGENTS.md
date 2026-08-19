# gitee-mcp

MCP server bridging **Gitee** (gitee.com), China's largest open-source
platform: humming radar, momentum, repo intel, user/repo search, zh->en
translation via local LLM, webhook feed, watchlist, ecosystem graph,
GitHub mirror, README corpus. Backend FastMCP 3.4.4 + FastAPI on **11161**,
React webapp on **11162**. Anonymous tier works out of the box (60 req/hr,
cached); GITEE_TOKEN unlocks search.

## Reading order

1. `docs/ARCHITECTURE.md` - design, radar methodology, ecosystem layer, tiers
2. `docs/TOOLS.md` - full tool + REST reference
3. `SPEC.md` - v0.2 ecosystem-intelligence feature spec (what/why/deferred)
4. `src/gitee_mcp/` - source map below

## Directory map

```
src/gitee_mcp/
├── server.py        FastMCP + FastAPI app, REST routes, dual transport entry
├── server_state.py  shared FastMCP instance
├── config.py        env config, seed repos (one .env source of truth)
├── client.py        Gitee v5 client, anonymous/token tiers, activity_score
├── radar.py         humming radar (live commit/star/forks ranking)
├── cache.py         JSON TTL cache (data/cache)
├── translate.py     zh->en via Ollama + glossary fallback
├── llm.py           provider probe + chat completion proxy
├── history.py       radar snapshot history: momentum/star series/digest data (v0.2)
├── watchlist.py     persistent watchlist + change detection (v0.2)
├── stack.py         Chinese-OSS tech-stack fingerprint (v0.2)
├── release_notes.py latest-release summarizer (v0.2)
├── ecosystem.py     graph / GitHub mirror / weekly digest (v0.2)
├── corpus.py        README BM25 index (SQLite FTS5, RAG-lite) (v0.2)
├── feed.py          RSS 2.0 radar feed (v0.2)
├── search_expand.py cross-lingual query expansion (v0.2)
├── culture.py       "why it matters in CN OSS" explainer (v0.2)
├── errors.py        shared error_response() + tool annotations
├── skills/          gitee-expert SKILL.md
└── tools/           portmanteaus: explore, repo, search, translate_tool,
                     webhook_tool, watchlist_tool, ecosystem_tool,
                     corpus_tool, prefab, help_tool, shutdown_tool
```

## Entry points

- `gitee_mcp.server:main` - CLI (stdio default; --mode http)
- `gitee_mcp.server:app` - ASGI app (uvicorn)
- `run_server.py` - PyInstaller/MCPB entry, MCP_PORT/PORT switch

## Key rules

- Portmanteau tools with operation enums; Annotated+Field docs, no Args
- Never fabricate: anonymous repo search returns auth_required, not []
- Rate budget: anonymous 60 req/hr - tools default small, cache is 10 min
- `uv run python` only; PowerShell 7; ASCII in scripts (no em dashes)
- MCPB pack script wipes+recopies mcpb/src; prompts verified 3-4-100
- Git operations via gitops/git, never fileops

## Gate commands

```powershell
just ci          # ruff + pyright + pytest (cov>=60) + tsc + biome
just mcpb-pack   # fresh-stage bundle
just digest      # one-shot weekly ecosystem digest
```

## Next (reading order)

1. `src/gitee_mcp/client.py` - the API truth (what works anonymously)
2. `docs/TOOLS.md` - full tool + REST reference
3. `docs/CONFIGURATION.md` - env vars + local data stores
