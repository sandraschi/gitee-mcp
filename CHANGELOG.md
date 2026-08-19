# Changelog

## 0.1.1 - 2026-08-19

### Added

- `gitee_shutdown` self-termination tool + `POST /api/shutdown` endpoint
- `@mcp.prompt()` `gitee_research` discovery workflow template
- Tool annotations (`READ_ONLY` / `MUTATING` / `DESTRUCTIVE`) and
  `output_schema` on every tool
- Shared `error_response()` helper with `logger.exception()` auto-logging
- Dialogic `message` key on all tool success returns
- `@mcp.prompt()` template, coverage gate (`--cov-fail-under=60`), `T20`
  print-ban in ruff, `pytest-cov` and `pre-commit` dev deps
- Pre-commit infra: `.pre-commit-config.yaml`, `scripts/pre-commit-biome.ps1`,
  `.gitattributes` (eol=lf), `just bootstrap`
- Session-context injection: `.claude-plugin/`, `hooks/hooks.json`,
  `.cursorrules` Session Context section, `.windsurfrules`,
  `.github/copilot-instructions.md`, `.opencode/skills/`, `.agents/skills/`
- `renovate.json` (stabilityDays 3, Monday schedule)
- Webapp: shared `API_BASE` (no hardcoded backend URLs), data-testid on
  Help/ApiDocs/Logs/Inbox, 6 chat example prompts, Ctrl+0 zoom reset

### Fixed

- CI now passes: `oven-sh/setup-bun@v2` (bun was not on runner PATH),
  `astral-sh/setup-uv@v3`, `bun install --frozen-lockfile`, `bun run biome:ci`
- MCPB 3-4-100 prompts: system.md 2053 -> 3092 words, user.md 2225 -> 4173
  words (pack gate now passes)
- `mcp-central-docs/starts/gitee-mcp-start.bat` rewritten to relative path
  with `%*` passthrough; registered in starts/README.md + fleet manifest
- `reports/` added to `.gitignore`

## 0.1.0 - 2026-08-18

Initial release.

### Added

- `gitee_explore` portmanteau: humming radar (anonymous, real commit/star/
  forks data), top-starred/top-forked (token), seed recommend/refresh
- `gitee_repo` portmanteau: details, readme, languages, commits, contents,
  branches - all anonymous
- `gitee_search` portmanteau: users (anonymous), repos (token),
  user_repos (anonymous)
- `gitee_translate` portmanteau: zh->en via local Ollama with honest
  dictionary-gloss fallback
- `gitee_webhook` portmanteau + POST /api/webhooks/gitee receiver with
  X-Gitee-Token secret check
- Prefab cards: `show_gitee_humming_card`, `show_gitee_status_card`
- FastAPI REST surface on 11161: health, diagnostics, capabilities, tools,
  skills, dashboard, radar, repo surfaces, search, translate, llm chat/
  discover, logs, webhooks
- React webapp on 11162: Dashboard, Trending, Search, Repo, Chat (skill-
  first, 4 personalities), Skills, Inbox, API Docs, Settings, Help, Logs
- Dual transport: stdio default, HTTP via MCP_PORT/PORT (run_server.py)
- JsonCache (data/cache, TTL 600s) to protect the anonymous rate budget
- MCPB packaging: manifest, 256px icon, 3-4-100 prompts (113 examples),
  fresh-stage pack script with verification
- CI workflow (Windows): ruff, pyright, pytest, tsc, biome
- Tests: 17 pytest cases (respx doubles), 12 Playwright e2e cases
- Docs stack: README, INSTALL, ONBOARDING, WRAPPEE, ARCHITECTURE,
  CONFIGURATION, TOOLS, DEVELOPMENT, TROUBLESHOOTING

### Verified constraints

- Gitee v5 anonymous surface probed live (repo/readme/languages/commits/
  branches/contents/users search, 60 req/hr)
- Explore/trending pages confirmed unscrapable (405 anti-bot), repo search
  confirmed token-gated - both documented and handled honestly
