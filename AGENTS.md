# gitee-mcp

MCP server bridging **Gitee** (gitee.com), China's largest open-source
platform: humming radar, repo intel, user/repo search, zh->en translation
via local LLM, webhook feed. Backend FastMCP 3.4.4 + FastAPI on **11161**,
React webapp on **11162**. Anonymous tier works out of the box (60 req/hr,
cached); GITEE_TOKEN unlocks search.

## Reading order

1. `docs/ARCHITECTURE.md` - design, radar methodology, tiers
2. `docs/TOOLS.md` - full tool + REST reference
3. `src/gitee_mcp/` - source map below

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
├── skills/          gitee-expert SKILL.md
└── tools/           portmanteaus: explore, repo, search, translate_tool,
                     webhook_tool, prefab, help_tool (imported in __init__)
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
just ci          # ruff + pyright + pytest + tsc + biome
just mcpb-pack   # fresh-stage bundle
```

## Next (reading order)

1. `src/gitee_mcp/client.py` - the API truth (what works anonymously)
2. `src/gitee_mcp/tools/AGENTS.md` - tool layer details
3. `webapp/AGENTS.md` - frontend structure
