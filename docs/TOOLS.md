# Tool Reference

## gitee_explore

Discovery portmanteau - "what is humming on Gitee".

| Operation | Tier | Description |
|-----------|------|-------------|
| `humming` | anonymous | Ranked live radar: activity_score, stars, forks, language, recent commits per repo. Filters: `limit` (1-50), `language`, `translate` |
| `top_starred` | token | Repo search sorted by stars |
| `top_forked` | token | Repo search sorted by forks |
| `recommended` | any | The configured seed list |
| `refresh` | any | Re-verify seeds against the live API; report dead ones |

Example:
```
gitee_explore(operation="humming", limit=10, language="Python", translate=True)
```

## gitee_repo

Repository intel portmanteau. All operations anonymous.

| Operation | Returns |
|-----------|---------|
| `details` | Full metadata (pruned of heavy nested objects), normalized html_url |
| `readme` | Decoded README markdown (None when absent; truncated at 60k chars) |
| `languages` | [{language, color, percent, bytes}] |
| `commits` | Recent commits (limit 1-100): sha, message, author, date |
| `contents` | File/dir listing for `path` |
| `branches` | Branch names |

Example:
```
gitee_repo(operation="details", owner="dromara", repo="hutool")
```

## gitee_search

| Operation | Tier | Description |
|-----------|------|-------------|
| `users` | anonymous | Search users by login/name |
| `repos` | token | Keyword repo search, sort by stars/forks/updated/pushed |
| `user_repos` | anonymous | Public repos of a login, sorted by push time |

## gitee_translate

| Operation | Tier | Description |
|-----------|------|-------------|
| `zh_to_en` | any | Chinese -> English via local LLM; glossary fallback flagged `translated: false` |
| `detect` | any | CJK detection for input text |
| `status` | any | LLM provider health, base URL, model |

## gitee_webhook

| Operation | Description |
|-----------|-------------|
| `list` | Recent inbound events with one-line summaries |
| `clear` | Wipe the event store |

## Prefab cards

| Tool | Purpose |
|------|---------|
| `show_gitee_humming_card` | Radar as rich in-chat card (plain text fallback included) |
| `show_gitee_status_card` | Tier, rate limit, LLM health, model, seeds |

## gitee_help

Static documentation covering tools, tiers, configuration, notes.

## gitee_shutdown

Graceful self-termination. `gitee_shutdown(confirm=True)` stops the server
after a short delay so the in-flight response flushes. Also exposed as
`POST /api/shutdown` in HTTP mode. Annotated DESTRUCTIVE.

## gitee_watchlist (v0.2)

Persistent repo watchlist with change detection.

| Op | Purpose |
|----|---------|
| `add` | Watch a repo (optional `min_activity` auto-follow threshold) |
| `remove` | Stop watching |
| `list` | Show watched repos |
| `check` | Diff recent commits vs last check; report new activity |

State persists in `data/watchlist.json`.

## gitee_ecosystem (v0.2)

Ecosystem intelligence.

| Op | Purpose |
|----|---------|
| `graph` | Org / repo / fork-family graph (scope=seeds\|watchlist) |
| `mirror` | Compare a repo against its GitHub twin (cached 1h) |
| `digest` | Weekly "who's rising" narrative from radar history (writes `data/digest-latest.md`) |
| `feed` | RSS 2.0 feed of the humming radar |

## gitee_corpus (v0.2)

README keyword corpus (RAG-lite, SQLite FTS5).

| Op | Purpose |
|----|---------|
| `search` | BM25 keyword search over indexed READMEs |
| `ingest` | Fetch + index one repo's README |
| `status` | Indexed count + sample |

READMEs are auto-indexed when fetched via `gitee_repo(readme)`.

## Prompts

- `gitee_research`: discovery workflow (radar -> repo profile -> readme ->
  translate).
- `gitee_weekly_brief`: weekly "who is rising" briefing from momentum +
  digest.
- `gitee_adoption_assessment`: velocity/mass/stack/docs verdict for one
  project.
- `gitee_compare_projects`: head-to-head comparison of two repos.

## REST surface (webapp backend)

| Route | Purpose |
|-------|---------|
| `GET /api/health` | Status, version, uptime, tool_count, tier, providers |
| `GET /api/v1/diagnostics` | Tool list + system info (CUA smoke-test contract) |
| `GET /api/capabilities` | Feature flags |
| `GET /api/tools` | Registered tool names |
| `GET /api/skills` / `GET /api/skills/{name}` | Skill list + content |
| `GET /api/dashboard` | KPI data |
| `GET /api/explore/humming` | Radar (limit, language, translate params) |
| `GET /api/repos/{owner}/{repo}/{surface}` | details/readme/languages/commits/contents/branches |
| `GET /api/search/users` / `GET /api/search/repos` | Search |
| `POST /api/translate` | {text, target_lang} -> translation |
| `GET /api/translate/status` | LLM provider health |
| `POST /api/llm/chat` | Chat completion proxy |
| `GET /api/llm/discover` | Ollama/LM Studio probe |
| `POST /api/webhooks/gitee` | Webhook receiver (X-Gitee-Token check) |
| `GET /api/logs` | Ring-buffer log tail (level filter) |
| `POST /api/shutdown` | Graceful self-termination |
| `GET /api/webhooks/events` | Webhook feed |
| `DELETE /api/webhooks/events` | Clear webhook feed |
| `GET /api/webhooks/digest` | Grouped webhook digest (since_hours) |
| `GET /api/explore/momentum` | Top activity movers (7d delta) |
| `GET /api/repos/{o}/{r}/stack` | Chinese-OSS tech-stack fingerprint |
| `GET /api/repos/{o}/{r}/releases` | Latest releases + English summary |
| `GET /api/repos/{o}/{r}/star-history` | Observed stars/forks/activity series |
| `POST /api/translate/explain` | Culture notes (why it matters in CN OSS) |
| `GET /api/watchlist` / `POST` / `DELETE` | Watchlist CRUD |
| `POST /api/watchlist/check` | Watchlist change detection |
| `GET /api/ecosystem/graph` | Org/repo/fork graph (scope=seeds\|watchlist) |
| `GET /api/ecosystem/mirror/{o}/{r}` | GitHub mirror comparison |
| `GET /api/ecosystem/digest` | Weekly narrative digest (days) |
| `GET /api/feed.xml` | RSS 2.0 radar feed |
| `GET /api/corpus/search` | README BM25 keyword search |
| `GET /api/corpus/status` | Corpus index status |
| `/mcp` | MCP streamable HTTP |
| `/docs` | Swagger UI |

## Error contract

All tools return `success: bool`; failures carry `error`, `error_type`
(`not_found`, `auth_required`, `auth_invalid`, `rate_limited`,
`network_error`, `validation`) and `suggestions`.
