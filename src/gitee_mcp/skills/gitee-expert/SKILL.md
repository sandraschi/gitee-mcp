# Gitee Expert - using gitee-mcp well

You have access to Gitee (gitee.com), China's largest GitHub-style platform.
This skill teaches the effective workflows for discovery, intel, translation
and webhook monitoring.

## What the server does

- **Discovery**: `gitee_explore` - the "humming" radar ranks popular seed
  repos by real commit/star/forks activity (works anonymously, rate-limited
  to ~60 requests/hour, responses are cached ~10 minutes). Token tier adds
  top-starred / top-forked via repo search.
- **Intel**: `gitee_repo` - details, README, languages, commits, file
  contents and branches for any public repo.
- **Search**: `gitee_search` - users (anonymous) and repos (token tier).
- **Translation**: `gitee_translate` - Chinese to English via a local LLM
  (Ollama). Falls back to a dictionary gloss honestly flagged as partial.
- **Webhooks**: `gitee_webhook` - feed of inbound push/star/fork events.

## Workflows

### 1. "What is humming on Gitee?"

Call `gitee_explore(operation="humming", limit=10)` first. Repos carry
`activity_score`, `stargazers_count`, `forks_count`, `language`,
`pushed_at` and recent commits. For a language focus pass
`language="Python"`. For bilingual summaries pass `translate=True` - this
invokes the local LLM per repo, so use it with limit <= 10.

### 2. Dig into one repo

`gitee_repo(operation="details", owner=..., repo=...)` first, then
`languages` for the tech mix, `readme` for the story, `commits` for recent
velocity. READMEs are often Chinese - gloss with `gitee_translate`.

### 3. Find a user or project

`gitee_search(operation="users", query=...)` works without a token.
Repo search requires GITEE_TOKEN; the tool returns an actionable hint when
it is missing - do not fake results.

### 4. Track events

If the user configured a repo webhook, `gitee_webhook(operation="list")`
shows push/star/fork events with a one-line summary each.

## Important notes

- **Rate limits**: anonymous tier is 60 requests/hour. Prefer `limit` <= 20
  and avoid translate=True on large lists unless the user asked for it.
- **Honesty**: anonymous tier cannot return the platform trending page
  (Gitee blocks scraping). The radar's seed-based ranking is real data, not
  a simulation - dead seeds are dropped and reported.
- **Chinese content**: descriptions are commonly Chinese; translation is
  best-effort and flagged when the provider is unavailable.
- **Tier upgrade**: one line in `.env` (`GITEE_TOKEN=...`, free, no credit
  card) unlocks repo search and higher limits.
