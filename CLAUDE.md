# gitee-mcp - agent instructions

Bridge to Gitee (gitee.com), China's largest open-source platform.

## Commands

- Start: `start.bat` (backend 11161 + webapp 11162) or `just serve`
- Tests: `just test` (pytest), `just ci` (all gates)
- Lint: `just lint`, format: `just fmt`, types: `just types`
- Webapp: `cd webapp && bun install && bun run dev`
- Bundle: `just mcpb-pack`

## Key facts

- Anonymous tier is real data (repo details/readme/languages/commits,
  user search), rate-limited ~60 req/hour; responses cached 10 min.
- Repo search + top-starred need GITEE_TOKEN (free).
- Gitee trending pages are NOT scrapable (405 anti-bot) - the radar is
  computed from live repo data; never claim it is Gitee's trending list.
- Translation uses local Ollama; gloss fallback is honest
  (translated: false).
- Don't add em dashes, don't use naked `python` (use `uv run python`).
- Don't commit node_modules/.venv/data/.env/*.bak - all gitignored.
