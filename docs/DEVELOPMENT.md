# Development Setup

## Tools Required

Install all of these before continuing:

```bash
# Windows (winget)
winget install astral-sh.uv
winget install Git.Git
winget install OpenJS.NodeJS
winget install Casey.Just
winget install Oven-sh.Bun

# Verify
uv --version
git --version
node --version
just --version
bun --version
```

## Setup

```bash
git clone https://github.com/sandraschi/gitee-mcp
cd gitee-mcp
uv sync
cd webapp && bun install && cd ..
```

## Onboarding status

Onboarding is required (Gitee account + free token are the wrappee/account
side of this bridge). See [docs/ONBOARDING.md](ONBOARDING.md). Anonymous
mode is a fully functional real-data tier, not a mock.

## Common Tasks

```bash
just serve      # full stack (start.ps1): backend 11161 + webapp 11162
just test       # pytest (coverage gate --cov-fail-under=60)
just lint       # ruff check + format check
just types      # pyright
just tsc        # webapp TypeScript check
just biome      # webapp Biome check
just digest     # one-shot weekly ecosystem digest (writes data/digest-latest.md)
just ci         # all gates locally
just mcpb-pack  # fresh-stage MCPB bundle with 3-4-100 verification
```

## Code Standards

- FastMCP 3.4.4+ (fleet minimum), portmanteau tools with operation enums
- Docstrings: `## Return Format` + `## Examples`, `Annotated` + `Field`
  (no `Args:` blocks)
- Prefab `@mcp.tool(app=True)` for list/status tools
- `uv run python` never naked `python`; PowerShell 7, ASCII only in scripts
- Fleet standards: `D:\Dev\repos\mcp-central-docs\standards\`

## Test structure

- `tests/test_gitee.py` - client/radar/translate units (respx doubles)
- `tests/test_api.py` - REST surface via TestClient (respx doubles)
- `tests/test_intelligence.py` - v0.2 ecosystem modules: history/momentum,
  stack, search expansion, culture, watchlist, releases, feed, ecosystem
  graph/mirror/digest, corpus (all offline, respx doubles)
- `tests/test_intelligence_api.py` - v0.2 REST endpoints + tool registration
- `webapp/e2e/fleet-audit.spec.ts` - Playwright: health, nav walk, radar,
  ecosystem page

Test doubles are declared: all HTTP mocking uses `respx` with explicit
routes. No live-network tests, no hidden fakes. On-disk state (radar
history, watchlist, corpus.db, cache) is cleared between tests via the
autouse fixture in `tests/conftest.py`. Coverage gate: `--cov-fail-under=60`
(the suite currently sits ~68%).

## Contributing

1. Branch: `git checkout -b feat/your-thing`
2. `just ci` must pass locally (ruff, pyright, pytest, tsc, biome)
3. Commit conventional style, PR against `main`
