# Troubleshooting

## Server doesn't appear in Claude Desktop
**Cause**: Config JSON malformed or wrong path
**Fix**: Validate at jsonlint.com; check the `uv --directory` path matches your clone.

## "command not found: uv"
**Cause**: uv not installed or not in PATH
**Fix**: `winget install astral-sh.uv` then restart the terminal.

## Radar returns nothing / empty
**Cause**: Network blocked to gitee.com, or anonymous rate limit exhausted
**Fix**: `curl https://gitee.com/api/v5` must answer; check `data/cache`
TTL; wait for the hourly window or set `GITEE_TOKEN`.

## Tools report "auth_required"
**Cause**: The operation (repo search, top-starred) needs the token tier
**Fix**: Create a free token at gitee.com/profile/personal_access_tokens/new,
set `GITEE_TOKEN` in `.env`, restart.

## Tools report "rate_limited"
**Cause**: Anonymous quota (~60 req/hour) exhausted or HTTP 429
**Fix**: Wait for the window or set a token. The server caches 10 minutes to
stretch the budget.

## Tools report "auth_invalid" (401)
**Cause**: Token rejected by Gitee
**Fix**: Regenerate the token; ensure the `projects` scope is selected.

## Repo not found (404) for a repo that exists
**Cause**: Repo is private, or owner/repo spelling differs from the URL
**Fix**: Anonymous access only reaches public repos; check the gitee.com URL
path exactly.

## Translation returns gloss instead of full translation
**Cause**: Ollama not running or model missing
**Fix**: `winget install Ollama.Ollama`, `ollama serve`, `ollama pull qwen2.5:7b`.
Check `gitee_translate(operation="status")`.

## Webapp shows "Offline"
**Cause**: Backend on 11161 not running
**Fix**: Run `start.bat` (starts both). Check ports aren't taken:
`Get-NetTCPConnection -LocalPort 11161`.

## Backend fails to start on 11161
**Cause**: Port occupied by a zombie process
**Fix**: `Get-NetTCPConnection -LocalPort 11161 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`.

## Webhook events never arrive
**Cause**: Webhook URL unreachable from Gitee, or secret mismatch
**Fix**: The URL must be reachable from the internet (Tailscale/port-forward
for remote). Mirror the secret in `.env` as `GITEE_WEBHOOK_SECRET`.

## Chat page says "No local LLM detected"
**Cause**: Ollama (11434) or LM Studio (1234) not running
**Fix**: Start Ollama; re-probe on the Settings page. Or configure
`GITEE_LLM_BASE_URL` for a different provider.

## Rate limit meter is empty in Settings
**Cause**: No Gitee call has happened yet in this process
**Fix**: Run any tool once (e.g. open the Trending page), then re-check.

## Timestamps look off by a day
**Cause**: Gitee uses China Standard Time (+08:00)
**Fix**: Expected - the radar compares commit freshness in UTC.

## MCPB bundle import fails on a clean machine
**Cause**: Stale `mcpb/src` staging twin
**Fix**: Run `just mcpb-pack` - the script wipes and recopies `src/`
before packing.

## Momentum / digest says "no history yet"
**Cause**: Momentum and the weekly digest need at least two radar builds on
separate days to compute deltas
**Fix**: Run the radar (Trending page or `gitee_explore(operation="humming")`)
on different days. The first observation intentionally reports `momentum:
null` rather than a fake 0.

## Ecosystem graph shows few nodes
**Cause**: The graph only includes seed + watchlist repos
**Fix**: Add repos to the watchlist (`gitee_watchlist(add)` or the Ecosystem
page) to grow the graph. Contributor-overlap edges are intentionally not
included (they need the rate-heavy events API).

## Mirror compare says "not found on GitHub"
**Cause**: The project genuinely does not exist on GitHub (common for
Gitee-only Chinese projects), not a bug
**Fix**: Treat it as a signal: the project's community lives on Gitee only.

## Corpus search returns no matches
**Cause**: The README was never indexed (indexing happens when a README is
fetched via `gitee_repo(operation="readme")` or `gitee_corpus(ingest)`)
**Fix**: Run `gitee_corpus(operation="ingest", owner=..., repo=...)` for the
repos you care about, or fetch their READMEs once.

## Watchlist check says "error" for a repo
**Cause**: Repo 404 (gone/private) or rate-limited at check time
**Fix**: Verify the owner/repo spelling and tier; the entry stays in the
watchlist and is retried next check.

## `just digest` writes an empty brief
**Cause**: Not enough radar history yet
**Fix**: Same as the momentum case - run the radar on separate days first.
