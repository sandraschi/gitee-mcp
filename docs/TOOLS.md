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
| `GET /api/webhooks/events` | Webhook feed |
| `GET /api/logs` | Ring-buffer log tail |
| `POST /api/webhooks/events` (DELETE) | Clear webhook feed |
| `/mcp` | MCP streamable HTTP |
| `/docs` | Swagger UI |

## Error contract

All tools return `success: bool`; failures carry `error`, `error_type`
(`not_found`, `auth_required`, `auth_invalid`, `rate_limited`,
`network_error`, `validation`) and `suggestions`.
