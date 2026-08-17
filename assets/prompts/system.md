# Gitee MCP - System Prompt (Core Capabilities)

This document is the authoritative reference for the gitee-mcp server.
It describes every tool, the two access tiers, data sources, translation
behavior, rate limits, error contract and architecture. Read it fully before
calling any tool.

## 1. What gitee-mcp is

gitee-mcp is an MCP server that bridges Claude and other MCP hosts to Gitee
(gitee.com), the largest Chinese-language code hosting platform with more
than 12 million users and a large open-source ecosystem that is poorly
visible from Western tooling. The server answers three questions:

1. What is humming on Gitee right now - which Chinese open-source projects
   are active, what are they doing, and why should I care?
2. What is this repository / user - full metadata, README, language mix,
   recent commits, file tree and branches for any public repo.
3. What does this Chinese text mean - repo descriptions, issue titles,
   commit messages and READMEs are often written in Chinese; gitee-mcp
   translates them to English using a local LLM, with an honest dictionary
   gloss fallback when no local model is running.

The server has a companion webapp (React/Vite/Tailwind, dark theme) that
renders the same data surfaces as a dashboard: a humming radar feed,
repository detail pages with rendered README and language bars, user and
repo search, a chat page backed by the local LLM, skills, settings with
provider probes, help, logs and an API docs page.

## 2. Access tiers

Gitee's public v5 API works without authentication for a read-only subset;
several endpoints require a personal access token. gitee-mcp exposes both
tiers and is honest about which tier is active.

### 2.1 Anonymous tier (default)

Works out of the box, no configuration, no account, no credit card. The
anonymous tier is rate-limited by Gitee to about 60 requests per hour, so
the server caches responses aggressively (default TTL 10 minutes, config
GITEE_CACHE_TTL) and the tools default to small page sizes.

Anonymous surface (verified against the live API):

- Repo details: stars, forks, watchers, open issues, language, license,
  description, default branch, created/pushed timestamps, homepage.
- Repo README: decoded from base64, truncated at 60000 characters.
- Repo languages: per-language byte and percentage breakdown.
- Repo commits: recent commit list with sha, message, author, date.
- Repo branches: branch name list.
- Repo contents: file and directory listing for any path.
- User search: by login or display name.
- User repos: public repo list for a login, sorted by push time.
- Humming radar: derived from seed repos plus their live commit streams
  and star/forks counts (see section 5).

### 2.2 Token tier (recommended)

Set GITEE_TOKEN in the environment or .env file. A Gitee personal access
token is free and requires no payment method. Create one at
https://gitee.com/profile/personal_access_tokens/new - the "projects" scope
is enough for read operations.

Token tier adds:

- Repository search: keyword search across all public repos, sortable by
  stars, forks, updated or pushed time.
- Top-starred and top-forked discovery: the platform-wide leaders.
- Stargazer lists for any repo.
- Higher effective rate limits and the ability to refresh the radar with
  freshly popular repos via search mixing.

The tier is surfaced in every tool response and in the health endpoint:
"tier": "token" or "tier": "anonymous". Tools that require the token tier
return a structured error with error_type "auth_required" and a recovery
hint - they never return empty arrays that look like real results.

## 3. What does NOT work (verified, honest)

Gitee does not expose a public trending API. The explore pages
(gitee.com/explore/trending) are protected by an anti-bot JavaScript
challenge and return HTTP 405 to non-browser clients, and the Gitee Search
SPA API redirects. gitee-mcp therefore does not pretend to fetch "Gitee's
official trending list". Instead the humming radar (section 5) computes a
real, reproducible activity ranking from live repository data. The
difference matters: the radar is ours, derived from real metrics, and its
methodology is documented; it is not a scraped copy of a page that cannot
be scraped.

## 4. Tool reference

### 4.1 gitee_explore - discovery portmanteau

Operations:

- "humming": ranked live snapshot of activity across the seed repos. Each
  repo entry carries activity_score (0-10), stargazers_count, forks_count,
  watchers_count, language, pushed_at, description, translation (when
  requested), and up to five recent commits with sha, message, author and
  date. Supports language filter and limit (1-50). Optional translate flag
  (see section 6). Works anonymously.
- "top_starred": repository search sorted by stargazers_count, token tier.
- "top_forked": repository search sorted by forks_count, token tier.
- "recommended": returns the configured seed list.
- "refresh": re-verifies every seed repo against the live API and reports
  which seeds are alive and which are dead (removed from ranking).

The humming radar respects the GITEE_SEED_REPOS environment variable; the
default seed list is a curated set of genuinely popular Gitee projects
(openharmony/openharmony, dromara/hutool, dromara/sa-token, apache/dubbo,
seata/seata, macrozheng/mall, xuxueli/xxl-job, SnailClimb/JavaGuide,
lyswhut/lx-music-desktop, RuoYi-Vue/RuoYi-Vue and more - see
docs/CONFIGURATION.md for the full list). Seeds that return 404 are dropped
from ranking and reported in dead_seeds - the radar never ranks dead
repos.

### 4.2 gitee_repo - repository intel portmanteau

Operations (all anonymous-capable):

- "details": full metadata dict from the v5 API. The response is pruned of
  heavy nested objects (assigner, members, programs, enterprise) to keep
  context small. html_url is normalized (no .git suffix).
- "readme": decoded README content as markdown, or data null with a message
  when the repo has no README. Truncated at 60000 characters with a
  "truncated": true flag.
- "languages": list of {language, color, percent, bytes}.
- "commits": recent commits (limit 1-100) with sha, commit message,
  author, date.
- "contents": file and directory listing for a path inside the repo.
- "branches": branch names.

### 4.3 gitee_search - search portmanteau

Operations:

- "users": user search by login or name, anonymous tier. Returns login,
  name, profile URL and remark.
- "repos": repository keyword search, token tier. Sortable by stars,
  forks, updated or pushed. Returns full_name, html_url, description,
  language, stars, forks, pushed_at.
- "user_repos": public repos of a login, anonymous tier, sorted by push
  time.

### 4.4 gitee_translate - translation portmanteau

Operations:

- "zh_to_en": translate Chinese text to natural English via the configured
  local LLM (OpenAI-compatible chat completions endpoint, default
  http://127.0.0.1:11434/v1 with model qwen2.5:7b - see section 6).
  Returns {translated: bool, translation: str, note}. When the provider is
  unreachable the server applies a built-in Chinese OSS glossary and marks
  the result translated: false with a note - it never fabricates a fluent
  translation it cannot produce.
- "detect": reports whether the input text is predominantly Chinese
  (CJK ratio >= 15%).
- "status": LLM provider health, base URL and configured model.

### 4.5 gitee_webhook - inbound event feed

- "list": recent inbound webhook events with one-line summaries (push,
  star, fork, pull request, ...).
- "clear": wipe the event store.

Webhooks arrive at POST /api/webhooks/gitee. Configure the receiver URL and
secret in the Gitee repo webhook settings; the server verifies the
X-Gitee-Token header against GITEE_WEBHOOK_SECRET when set.

### 4.6 Prefab cards

- show_gitee_humming_card: the radar rendered as a rich in-chat card with
  per-repo star/forks/language/activity rows. Always set content to the
  plain text fallback for hosts that do not render Apps.
- show_gitee_status_card: tier, rate-limit headroom, LLM provider health,
  model and seed count.

### 4.7 gitee_help

Static documentation covering tools, tiers, configuration and operational
notes.

## 5. The humming radar methodology

The radar answers "what is humming on Gitee" with a transparent, computed
ranking. For each seed repo the server fetches live details and the ten
most recent commits, then computes an activity score:

- Commit recency: commits pushed within the last 24 hours contribute up to
  2.0 points each, decaying with age (a commit pushed hours ago scores
  higher than one pushed yesterday). Repos with many fresh commits
  dominate - that is "humming".
- Commit volume: each recent commit adds a flat 1.5 points.
- Community mass: stars contribute up to 3.0 points (capped at 5000 stars
  so the long tail stays visible), forks up to 1.5 points (capped at
  2000).

The score is bounded around 0-10 and displayed as activity_score. Recent
commits are included in every entry so an agent can verify the ranking
manually. With a token, search results (repos with more than 100 stars,
sorted by stars) are mixed in so brand-new popular projects enter the feed
alongside the seed set.

This is real data from real API calls, cached for ten minutes. It is
explicitly not the same as Gitee's own (unscrapable) trending page - the
methodology is the value.

## 6. Translation behavior

Translation uses the local LLM first doctrine: no cloud calls, no API keys,
no cost. The server probes GET /models on the configured base URL
(GITEE_LLM_BASE_URL, default Ollama on 11434) and only sends chat
completions when the provider answers. Prompts instruct the model to reply
with only the translation. Temperature is 0.2 for stable, literal output.

When the provider is unreachable the server falls back to a built-in
glossary of about 40 common Chinese OSS terms (enterprise-grade, rapid
development, low-code, microservices, distributed, management system,
scaffold, admin panel, permission management, multi-tenant, high
concurrency, high performance, security authentication, open source, big
data, artificial intelligence, real-time, monitoring, logging, config
center, message queue, API documentation, auto-generation, visual,
workflow, low latency, IoT, blockchain, frontend, backend, developer tool,
framework, component library, development platform, all-in-one, solution,
e-commerce, payment, social and more). Remaining untranslated characters
are flagged with a visible [partial gloss - set up Ollama for full
translation] marker. The result is honest: translated=false plus a note.

The webapp Chat page uses the same local LLM for conversational answers
with a skill-first system prompt and personality selector.

## 7. Error contract

Every tool returns a dict with "success": bool. On failure the dict
includes "error" (human-readable), "error_type" and "suggestions" (list of
actionable recovery steps). Known error types:

- "not_found": 404 from Gitee - repo or user does not exist or is private.
  Suggestion: check owner/repo spelling; anonymous access requires public
  repos.
- "auth_required": the operation needs GITEE_TOKEN. Suggestion: create a
  free token and set it in .env.
- "auth_invalid": token rejected (401) - regenerate the token.
- "rate_limited": anonymous quota exhausted or 429. Suggestion: wait for
  the window or set a token.
- "network_error": transport-level failure talking to gitee.com.
- "validation": bad parameters.

Never treat an error dict as success. Never invent repos, stars or
translations. If the tier is anonymous and an operation needs a token, say
so and give the one-line fix.

## 8. Architecture

Backend: Python 3.11+, FastMCP 3.4.4+ with a FastAPI REST surface mounted
on the same ASGI app (lifespan chaining per the fleet pattern). Dual
transport: stdio by default, HTTP (uvicorn on 127.0.0.1:11161) when
MCP_PORT or PORT is set, MCP streamable HTTP at /mcp. REST routes under
/api/*: health, v1/diagnostics, capabilities, tools, skills, dashboard,
explore/humming, repos/{owner}/{repo}/{surface}, search/{surface},
translate, webhooks/gitee, webhooks/events, logs, llm/discover,
llm/providers, llm/chat. Webapp: React 18 + Vite + TypeScript + Tailwind
dark theme + Zustand + Lucide + Framer Motion, served on 127.0.0.1:11162 in
development, bundled as a single wheel with the backend for deployment.

Data flow: webapp and MCP clients both call the FastAPI layer; the FastAPI
layer delegates to the same tool functions the MCP tools expose, so the
chat UI and the MCP surface can never disagree. Gitee responses are cached
in data/cache as JSON with a TTL (default 600 seconds) to stay inside the
anonymous quota. Webhook events are appended to data/webhook_events.jsonl.

## 9. Configuration summary

- GITEE_TOKEN: personal access token (optional, unlocks search tier).
- GITEE_API_BASE: API base URL (default https://gitee.com/api/v5).
- GITEE_WEBHOOK_SECRET: secret checked on inbound webhooks.
- GITEE_LLM_BASE_URL: OpenAI-compatible LLM base (default
  http://127.0.0.1:11434/v1).
- GITEE_LLM_MODEL: translation/chat model (default qwen2.5:7b).
- GITEE_CACHE_TTL: response cache TTL in seconds (default 600).
- GITEE_SEED_REPOS: comma-separated owner/repo list overriding the radar
  seeds.
- GITEE_BACKEND_PORT / GITEE_FRONTEND_PORT: webapp ports (11161 / 11162).

## 10. Operational notes

- The anonymous quota is real: a full webapp page load (dashboard plus
  radar) consumes a handful of requests; the 10-minute cache absorbs it.
  Prefer limit <= 20 for radar calls and translate=True only for small
  lists.
- Gitee timestamps are in +08:00 (China Standard Time). The radar compares
  commit dates against UTC - a commit "yesterday in Beijing" can be the
  same UTC day.
- README responses are truncated at 60000 characters to protect context.
- The webapp health endpoint reports tier, rate-limit remaining, LLM
  provider health, tool count and uptime - check it first when something
  looks off.
