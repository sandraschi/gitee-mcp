set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

# Start the full stack (backend + webapp) with the fleet start script
serve:
    ./start.ps1

# Run pytest suite
test:
    uv run pytest -q

# Ruff lint + format check
lint:
    uv run ruff check src/
    uv run ruff format src/ --check

# Auto-fix lint issues
fmt:
    uv run ruff check src/ --fix
    uv run ruff format src/

# Pyright typecheck
types:
    uv run pyright src/

# Webapp: TypeScript typecheck
tsc:
    cd webapp; bun run tsc --noEmit

# Webapp: Biome check
biome:
    cd webapp; bunx biome check src/

# Playwright e2e (starts its own backend)
e2e:
    cd webapp; bunx playwright test

# Local CI gate: lint + types + tests + tsc + biome
ci:
    uv run ruff check src/
    uv run ruff format src/ --check
    uv run pyright src/
    uv run pytest -q
    cd webapp; bun run tsc --noEmit
    cd webapp; bunx biome check src/

# Bundle for Claude Desktop (MCPB) - MUST wipe+recopy src -> mcpb/src first
mcpb-pack:
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File scripts/mcpb-pack.ps1

# Build the wheel
build:
    uv build

# Quick stdio smoke test of the MCP server
smoke:
    uv run python -c "from gitee_mcp.server import mcp; print('tools:', len(mcp._tool_manager._tools))"
