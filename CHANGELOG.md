# Changelog

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
