# Gitee MCP - User Guide and Tutorials

Welcome to gitee-mcp. This guide walks you through everything the server can
do, from your first hello to advanced workflows like building a personal
watchlist of Chinese open-source projects or monitoring CI pushes through
webhooks. Every section ends with concrete example prompts you can paste
into Claude.

## Part 1 - First steps

### 1.1 Your first call

The fastest way to see the value of the server is to ask for the humming
radar. Start a conversation with Claude and say:

"What is humming on Gitee right now?"

Claude will call gitee_explore with operation humming and present the top
repos: names, owners, languages, star counts, and recent commit activity.
Each entry includes a Chinese description - if you want it in English, say:

"Show me the same list but translate the descriptions to English."

Behind the scenes Claude calls gitee_explore with translate=True. The
server asks your local Ollama instance to translate each description. If
Ollama is not running, the server falls back to a dictionary gloss and
tells you so - it never silently fakes a translation.

### 1.2 Understanding what you see

A radar entry looks like this:

- Repo: macrozheng/mall (Java, 42000 stars, 17000 forks)
- Activity: 8.4
- Description: 一套基于SpringBoot+MyBatis的电商系统（包括前台商城系统及后台管理系统）...
- Recent commits: latest three commit messages with authors and dates.

The activity score is computed from real commit data: how fresh the recent
commits are, how many there are, and how much community mass (stars and
forks) the repo carries. A repo with a commit pushed two hours ago scores
higher than one with the same star count but no commits this week. The
recent commits are listed so you can verify the ranking yourself.

### 1.3 Anonymous vs token tier

The server works with zero configuration. Gitee's public API allows about
60 anonymous requests per hour; the server caches everything for ten
minutes so interactive use is comfortable.

You unlock more with a free token:

- Search repositories by keyword (anonymous search returns nothing on
  Gitee - the server tells you this honestly instead of showing empty
  results).
- See the top-starred and top-forked repos platform-wide.
- Higher rate limits.
- Fresh popular repos mixed into the radar feed.

Creating the token takes two minutes and no payment method:
gitee.com/profile/personal_access_tokens/new - select the "projects" scope,
copy the token, paste it into your .env file as GITEE_TOKEN=... and restart
the server. Full instructions are in docs/ONBOARDING.md.

## Part 2 - Discovery workflows

### 2.1 The morning scan

A great habit: every morning, ask for a focused radar read.

"Show me the 10 most active Java repos on Gitee right now."

"Which Python projects are humming on Gitee this week?"

"Any Gitee projects in my favorite tech: Rust, Go or TypeScript? Show the
top 15 with activity scores."

Claude filters the radar by language for you. If the filter returns few
results, remember the seed set is curated; with a token you can also ask:

"What are the top 20 most starred repos on Gitee?"

That switches to the token-tier search sorted by stars, which covers the
entire platform, not just the seeds.

### 2.2 Following the Chinese open-source ecosystem

Chinese OSS has its own heavyweight communities that are mostly invisible
on GitHub: dromara (hutool, sa-token, RuoYi-Vue-Plus), openharmony
(Huawei's OS), macrozheng (mall), YunaiV (ruoyi-vue-pro) and the Alibaba
stack (nacos, dubbo, seata). Ask Claude:

"Summarize the dromara organization - which of their projects are most
active on Gitee and what do they do?"

"Compare the activity of openharmony/openharmony with apache/dubbo."

"Which Gitee projects are related to microservices? List their repos and
translations."

### 2.3 Building a personal watchlist

The radar seed list is configurable. In .env:

GITEE_SEED_REPOS=macrozheng/mall,dromara/hutool,halo-dev/halo

Then every radar call ranks exactly the repos you care about. You can also
ask Claude for a one-off watchlist without touching config:

"Check the activity of these repos: apache/skywalking, baomidou/mybatis-
plus, Tencent/APIJSON. What changed in each in the last 24 hours?"

Claude will call gitee_repo with operation commits for each.

### 2.4 Discovering users

Looking for a Chinese developer, company or organization?

"Find the Gitee user 'macrozheng'."

"Search for users named 'Jackson' on Gitee."

"What public repos does the user 'hutool' have?"

The first two use gitee_search users, the third uses user_repos. User
search works anonymously, so this is a reliable entry point.

## Part 3 - Repository deep dives

### 3.1 The profile

For any public repo:

"Give me a full profile of dromara/hutool: description, stars, forks,
language, license, last push, and what it is."

"Profile the repo SnailClimb/JavaGuide and summarize its README for me."

Claude uses gitee_repo details and readme. READMEs are frequently Chinese;
ask "and translate the README highlights" to gloss them through the local
LLM.

### 3.2 Language mix

"Show the language breakdown of macrozheng/mall as percentages."

"Which languages dominate openharmony/openharmony?"

gitee_repo languages returns per-language bytes and percentages, which
Claude can render as a list or table.

### 3.3 Commit activity

"Show me the 10 most recent commits in seata/seata with authors and dates."

"What are the last 5 commits in xuxueli/xxl-job - any recent features or
fixes?"

Commits carry the author name, date and first line of the message - enough
for a velocity read. Chinese commit messages can be translated with
gitee_translate if they matter.

### 3.4 File tree

"What is in the docs folder of doocs/advanced-java?"

"List the top-level contents of YunaiV/ruoyi-vue-pro."

gitee_repo contents returns the directory listing for a path - useful for
orientation before reading files.

### 3.5 Branches

"Which branches does apache/dubbo have?"

## Part 4 - Search

### 4.1 Users (anonymous)

"Search Gitee users matching 'sandra'."

"Find the Gitee profile of the person who maintains lx-music-desktop."

### 4.2 Repos (token tier)

With a token:

"Search Gitee for repos about 'low code' sorted by stars."

"Find Java admin frameworks on Gitee with the most forks."

"Search Gitee repos for 'vue3' updated recently."

Without a token, Claude will explain that repo search needs the free token
and will not pretend to have results.

### 4.3 User repos

"List the public repos of user 'SnailClimb', newest pushes first."

## Part 5 - Translation

### 5.1 Translating descriptions

The radar and search responses include Chinese descriptions. Two ways to
get English:

- Pass translate=True on the radar call (one round trip).
- Translate any snippet directly: "Translate this to English: 企业级微服务
  快速开发框架，支持多租户、高并发、分布式事务。"

The second form calls gitee_translate zh_to_en directly - paste any
Chinese text (description, issue title, commit message).

### 5.2 Detecting Chinese

"Does this text contain Chinese: 'A microservices framework for rapid
development'?"

gitee_translate detect returns whether the text is predominantly Chinese.
Useful when cleaning scraped feeds.

### 5.3 Translation status

"Is the translation service available? Which model is configured?"

gitee_translate status reports provider health, base URL and model. If it
shows unreachable, start Ollama (ollama serve) or pull a model (ollama
pull qwen2.5:7b). Translation quality for Chinese tech text is good on
7B-class Qwen models.

### 5.4 The glossary fallback

No LLM? The server keeps a built-in glossary of about 40 common Chinese
OSS terms (enterprise-grade, low-code, microservices, distributed, admin
panel, permission management, multi-tenant, high concurrency, and more).
Untranslated leftovers are visibly flagged. This keeps output readable
without pretending to be a real translation.

## Part 6 - Webhooks

### 6.1 Configuration

1. Create a Gitee webhook in your repo: repo page -> Management -> Web
   Hooks -> Add Web Hook.
2. URL: http://127.0.0.1:11161/api/webhooks/gitee (or the host running
   the server).
3. Set a secret and mirror it in .env as GITEE_WEBHOOK_SECRET.
4. Choose events: Push, Tag Push, Star, Fork, Pull Request.

### 6.2 Reading the feed

"What webhook events have been received lately?"

"What was the last push to my repo?"

"Clear the webhook event history."

gitee_webhook list summarizes each event in one line: who pushed how many
commits to which branch, who starred what, which repo was forked.

## Part 7 - The webapp

The bundled webapp (start it with start.bat, served on port 11162)
renders everything above as pages:

- Dashboard: server status, tier, rate-limit headroom, LLM health.
- Trending: the humming radar with language filter and translation toggle.
- Search: users and repos with a clear token-required state.
- Repo: full intel page with rendered README, language bar, commits,
  contents tree and branches.
- Inbox: webhook events.
- Chat: skill-first chat against your local LLM with four personalities.
- Skills: this skill rendered as markdown.
- Settings: health, token status, LLM provider probes (Ollama, LM Studio,
  custom), rate-limit meter.
- Help: architecture, ports, environment, troubleshooting.
- Logs: live backend ring buffer.
- API Docs: Swagger UI for the REST surface.

The webapp uses the exact same tool functions as the MCP surface, so what
you see in the browser is what Claude sees.

## Part 8 - Composed workflows

### 8.1 Research report on a Chinese OSS topic

"Write me a short briefing on Java microservices frameworks in the Chinese
open-source community. Use the Gitee radar for the Java filter, profile the
top three repos, summarize their READMEs, and translate the key points."

Claude chains: radar (language=Java) -> repo details -> readme -> gitee
translate. The result is a grounded briefing with real repos and real
numbers.

### 8.2 CI / push watch

"I want to know when openharmony pushes something big. Show the recent
commits and tell me if any landed in the last day."

"Watch my configured webhook feed and summarize today's push activity."

### 8.3 Comparing two projects

"Compare dromara/hutool and baomidou/mybatis-plus: stars, forks, language
mix, recent commit velocity and README positioning. Which looks healthier?"

### 8.4 Onboarding a teammate

"Brief my colleague on the Chinese Rust ecosystem on Gitee: top repos,
what they do, how active they are. Translate everything."

## Part 9 - Common questions

### 9.1 Why is the radar different from Gitee's trending page?

Gitee's trending page cannot be fetched programmatically (anti-bot
protection, verified returning HTTP 405). The radar is our own ranking
computed from real commit, star and fork data of popular seed repos. It is
real data with a documented methodology - not a simulation, not a scrape.

### 9.2 Why do some repos have no translation?

Translation needs the local LLM. If Ollama is not running, descriptions
are glossed with the built-in dictionary and marked as partial. Start
Ollama and retry with translate=True.

### 9.3 Why does repo search say it needs a token?

Gitee returns an empty array for anonymous repo search - showing an empty
result would be a lie. The server instead explains that a free token
unlocks the search tier.

### 9.4 I hit the rate limit. What now?

Wait for the hourly window or set GITEE_TOKEN. The webapp dashboard shows
your remaining quota. Radar calls are cached for ten minutes, so reloading
the page does not cost quota.

### 9.5 The README is empty - is that a bug?

No - many repos have no README or a non-standard one. The server returns
data null with an explicit message.

### 9.6 Timestamps look odd?

Gitee timestamps are in China Standard Time (+08:00). The radar compares
commit freshness in UTC.

## Part 10 - Troubleshooting checklist

- The server starts but radar returns nothing: check data/cache and
  network reachability of gitee.com (curl https://gitee.com/api/v5).
- Tools report auth_required: set GITEE_TOKEN in .env, restart.
- Tools report rate_limited: anonymous quota exhausted; wait or token.
- Translation returns gloss instead of full translation: Ollama not
  reachable on 127.0.0.1:11434. Run ollama serve, pull qwen2.5:7b.
- Webhook events empty: verify the webhook URL, secret, and that the
  receiver endpoint is reachable from Gitee.
- Webapp cannot reach backend: backend on 11161, frontend on 11162; both
  must be up (start.bat starts both).

## Part 11 - Example dialogues

### Dialogue A - first use

User: What is humming on Gitee?
Claude: [calls gitee_explore humming, limit 10, no translation] Here are
the ten most active repos right now: macrozheng/mall (Java, 42k stars),
dromara/hutool (Java, 23k stars)... each with activity score and last
commit time.
User: Translate the Chinese descriptions.
Claude: [calls gitee_explore humming again with translate=True; Ollama is
running] Done - mall: "An e-commerce system built with SpringBoot and
MyBatis including storefront and admin panels."

### Dialogue B - no token, honest failure

User: Find repos about machine learning on Gitee.
Claude: [gitee_search repos] Repo search requires a Gitee token - the
anonymous tier cannot search repositories. Creating a free token takes two
minutes: gitee.com/profile/personal_access_tokens/new, then set
GITEE_TOKEN in .env. Alternatively I can show you the humming radar
filtered by language, or search Gitee users.

### Dialogue C - deep dive

User: Tell me about openharmony/openharmony.
Claude: [details + languages + recent commits] openharmony/openharmony is
the open-source operating system by Huawei... language mix: C 60%, C++ 25%
... last 5 commits by [authors] on [dates]. The README is in Chinese - want
a translated summary?
User: Yes.
Claude: [readme + zh_to_en] Key points: ...

## Part 12 - Keeping the server healthy

- Restart after changing .env values.
- Run the seed refresh periodically: "Refresh the Gitee radar seeds" -
  dead seeds are reported and dropped.
- Clear the webhook feed when it gets noisy.
- The data directory (data/cache, data/webhook_events.jsonl) is safe to
  delete - it is only a cache and event log.

That is the complete tour. The fastest way to learn is to ask the radar
question right now - the data is live.

## Part 13 - Advanced workflows

### 13.1 A full ecosystem briefing

A richer variant of the research report. Ask:

"Produce a briefing on the Chinese microservices ecosystem: use the Gitee
radar filtered to Java, profile the five most active repos, summarize each
README, translate the key points, and close with which ones look most
maintainable and why."

Claude chains radar -> details -> readme -> translation, then reasons over
the collected facts. Because every number comes from a real API call, the
briefing is grounded - there are no invented stats.

### 13.2 Readiness review of a project

"Assess dromara/sa-token for adoption: how active are the commits, how
many stars and forks, what is in the README, and does the language mix look
healthy?"

The pieces: commits (velocity), details (community mass), languages
(health), readme (positioning). Claude combines them into a verdict with
evidence.

### 13.3 Watchlist diffs over time

On a first session:

"Remember this watchlist: apache/skywalking, baomidou/mybatis-plus,
Tencent/APIJSON. I will ask about it again."

On later sessions:

"Check my watchlist - what changed in the last 48 hours?"

Each check re-reads the commit streams and reports what is fresh. This is
the closest thing to a Gitee notification feed you get without webhooks.

### 13.4 Chinese tech stack research

"Which Gitee projects cover the typical Chinese enterprise Java stack -
RBAC, workflow, ORM, monitoring? For each, show repo, stars and a one-line
description in English."

Claude maps concepts to known projects (RuoYi for RBAC/admin, xxl-job for
scheduling, mybatis-plus for ORM, skywalking for monitoring) and verifies
against live data rather than trusting memory.

## Part 14 - Operational runbooks

### 14.1 Onboarding a new Gitee token

1. Open https://gitee.com/profile/personal_access_tokens/new.
2. Select the "projects" scope (read operations are enough).
3. Copy the token into .env: GITEE_TOKEN=...
4. Restart the server.
5. Verify with gitee_translate status or the health endpoint - the tier
   flips to token and repo search starts working.

### 14.2 Refreshing the radar seeds

The default seed list is curated. To adapt it: set GITEE_SEED_REPOS in .env
(comma-separated owner/repo), restart, then call the refresh operation.
Dead seeds are reported and dropped - the radar never ranks repos that 404.

### 14.3 Monitoring CI through webhooks

Point a repo webhook at POST http://host:11161/api/webhooks/gitee with a
secret mirrored in GITEE_WEBHOOK_SECRET, subscribe to Push events, then ask
"what has been pushed to my repos today" to read the feed.

## Part 15 - REST API usage for developers

The same surfaces are available over HTTP on port 11161 (the webapp
proxies /api). Examples:

# Health
curl http://127.0.0.1:11161/api/health

# Radar, 10 results, Java only, translated
curl "http://127.0.0.1:11161/api/explore/humming?limit=10&language=Java&translate=true"

# Repo intel
curl http://127.0.0.1:11161/api/repos/dromara/hutool/details
curl http://127.0.0.1:11161/api/repos/dromara/hutool/commits?limit=5

# Search (users anonymous, repos need token)
curl "http://127.0.0.1:11161/api/search/users?q=macrozheng"
curl "http://127.0.0.1:11161/api/search/repos?q=low-code"

# Translate
curl -X POST http://127.0.0.1:11161/api/translate -H "Content-Type: application/json" -d "{\"text\":\"企业级微服务快速开发框架\"}"

# Chat with the local LLM
curl -X POST http://127.0.0.1:11161/api/llm/chat -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}"

# Webhook receive + feed
curl -X POST http://127.0.0.1:11161/api/webhooks/gitee -H "X-Gitee-Event: Push Hook" -d '{}'
curl http://127.0.0.1:11161/api/webhooks/events

Interactive documentation: http://127.0.0.1:11161/docs (Swagger UI).

## Part 16 - Deep troubleshooting

### 16.1 The radar is empty but health is ok

Likely cause: the anonymous quota is exhausted for this hour. Check the
rate-limit numbers on the dashboard. Fix: wait for the window, set
GITEE_TOKEN, or reduce the seed set.

### 16.2 Translation always returns gloss

Ollama is not reachable. Verify with gitee_translate status, then:
ollama serve; ollama pull qwen2.5:7b. If you use a different provider, set
GITEE_LLM_BASE_URL and GITEE_LLM_MODEL and restart.

### 16.3 Webhooks are not arriving

Check that the webhook URL is reachable from the internet (not just
localhost), the secret matches, and the server is in HTTP mode on the
expected port. Events land in data/webhook_events.jsonl - inspect that file
to see raw payloads.

### 16.4 The webapp shows "Offline"

The backend on 11161 is down. Run start.bat (starts both) and wait for the
health check to pass; the UI auto-reconnects.

### 16.5 Nothing works after an upgrade

Delete data/cache (safe - it is only a cache) and restart. Stale cached
responses across a version change are the usual suspect.

## Part 17 - FAQ extended

### 17.1 Can I get push notifications without polling?

Not from Gitee directly - the platform has no outbound notification API.
The two supported patterns are webhooks (server-side, real-time) and
session watchlists (agent-side, on-demand). Both are covered above.

### 17.2 Does gitee-mcp store my token?

Only in your .env file on your machine. The server reads it at startup and
sends it as an access_token query parameter to gitee.com. It is never
written to logs, cache, or the webhook store.

### 17.3 Is the radar data real?

Yes - every entry comes from live Gitee API calls (details + commits) for
the seed repos. The activity score is a documented formula over that data,
not a guess and not Gitee's (unscrapable) trending page.

### 17.4 Why does repo search need a token?

Gitee returns an empty array for anonymous repository search. Returning an
empty result would be misleading, so the server explicitly asks for the
free token instead. User search is genuinely anonymous.

### 17.5 Can I translate to other languages?

Currently only zh -> en. Non-English target languages return a validation
error. Chinese issue titles and commit messages are the primary use case.

## Part 18 - Glossary of common Chinese OSS terms

A quick decoder ring for descriptions you will meet:

- 企业级: enterprise-grade
- 微服务 / 分布式: microservices / distributed
- 低代码 / 可视化: low-code / visual
- 管理系统 / 后台管理: management system / admin panel
- 权限管理 / 多租户: permission management / multi-tenant
- 高并发 / 高性能: high concurrency / high performance
- 大数据 / 人工智能: big data / artificial intelligence
- 实时 / 监控 / 日志: real-time / monitoring / logging
- 配置中心 / 消息队列: config center / message queue
- 接口文档 / 自动生成: API documentation / auto-generation
- 工作流 / 脚手架: workflow / scaffold
- 物联网 / 区块链: IoT / blockchain
- 前端 / 后端: frontend / backend
- 框架 / 组件库: framework / component library
- 一站式 / 解决方案: all-in-one / solution
- 电商 / 支付: e-commerce / payment

The server applies this same glossary when the local LLM is offline, so
you get a readable gloss even without Ollama.

## Part 19 - Metrics worth tracking

For anyone following the Chinese OSS world, the radar gives three cheap
signals:

- Commit velocity: repos with fresh, frequent commits are alive. A repo
  with high stars but no commits this week may be dormant.
- Star/forks mass: community adoption. Compare against the same project on
  GitHub to see where its users actually live.
- Language mix: tells you the implementation stack at a glance (Java and
  Vue dominate the Chinese enterprise admin space).

Ask the radar weekly and you build a picture of who is rising and who is
stalling - without ever hitting the quota.

That is everything. Go explore - the Chinese open-source world is live and
humming.

## Part 20 - Security and privacy

### 20.1 What leaves your machine

Every Gitee API call goes to gitee.com/api/v5. Translation and chat go to
your local LLM (default http://127.0.0.1:11434/v1) - nothing is sent to a
cloud AI provider. No telemetry is collected. The only outbound traffic is
to Gitee itself and (optionally) your local Ollama.

### 20.2 Your token

GITEE_TOKEN lives only in your .env file. It is sent to gitee.com as an
access_token parameter and is never logged, cached, or stored in the
webhook event file. Keep .env out of git (it is gitignored) and never paste
the token into chat.

### 20.3 Webhook secrets

If you set GITEE_WEBHOOK_SECRET, the receiver rejects requests whose
X-Gitee-Token header does not match. Choose a long random value and reuse
it on the Gitee webhook configuration page.

### 20.4 Local data

data/cache (JSON cache) and data/webhook_events.jsonl (webhook log) are the
only on-disk artifacts. Both are gitignored and safe to delete - they are
regenerable. The webhook log may contain real commit/star payloads; treat
it as sensitive if your repos are private.

## Part 21 - Companion webapp tips

The webapp shares the backend with the MCP tools, so anything you learn in
the browser works in Claude too.

- The Dashboard health card is the fastest way to see tier and quota.
- Trending supports a language filter and a translate toggle - set both and
  bookmark the URL for your daily scan.
- The Repo page renders READMEs as markdown and shows the language bar;
  deep links into it from search and radar are shareable.
- Chat has four personalities (Research Assistant, Expert Reviewer, Quick
  Summarizer, Custom) and remembers history in the browser - use Custom to
  paste your own system prompt.
- Settings probes Ollama, LM Studio and your custom endpoint, and lets you
  pick the provider and model used by the chat page.
- Logs is a live ring buffer of the backend logger - the first place to
  look when something behaves oddly.

## Part 22 - Keyboard-friendly and accessibility notes

The webapp is dark by default (zinc-950) with high-contrast amber accents.
Ctrl+scroll zooms the whole UI (persisted), and Ctrl+0 resets the zoom.
Form controls (selects, inputs, textareas) follow the dark scheme. If you
prefer another LLM for chat, set it in Settings - the choice is remembered
in the browser.

## Part 23 - Example dialogues, continued

### Dialogue D - watchlist

User: Check apache/skywalking and Tencent/APIJSON - anything new in the
last two days?
Claude: [commits for both] skywalking: 3 commits in the last two days,
latest "[fix] adjust trace sampling"; APIJSON: no commits this week - it
looks quiet.
User: Keep watching those two for me.
Claude: Noted. In this session I will re-check them when you ask again;
for a persistent notification you would configure a Gitee webhook (see Part
6).

### Dialogue E - honest rate limit

User: What is humming on Gitee?
Claude: [radar returns throttled] The anonymous hourly quota for Gitee is
exhausted right now (0/60). Wait about an hour, or set a free GITEE_TOKEN
in .env to unlock the full tier and refresh immediately. I can also search
users anonymously while we wait.
User: Set the token later; show me the user search for "macrozheng".
Claude: [users search] Here are the matches...

### Dialogue F - comparing repos

User: dromara/hutool vs baomidou/mybatis-plus - who is healthier?
Claude: [details + commits + languages for both] hutool: 23k stars, 9k
forks, active commits this week, Java 99%; mybatis-plus: 20k stars, 8k
forks, fewer commits this week, Java 100%. Both healthy; hutool has more
recent velocity, mybatis-plus has a more focused scope. [A short verdict
with the numbers shown.]

## Part 24 - Known limitations

- Gitee trending pages cannot be fetched (anti-bot 405) - the radar is our
  computed ranking instead.
- Anonymous repo search is empty on Gitee's side - the server says so
  rather than lying.
- Only zh -> en translation is supported.
- The anonymous quota (about 60/hour) is real; caching absorbs interactive
  use but bulk scans need a token.
- Repo search results come from Gitee's search index, which is
  occasionally stale; the radar uses live repo details.

## Part 25 - Getting help

- The gitee_help tool: tools, tiers, configuration in one page.
- docs/TROUBLESHOOTING.md: common issues.
- docs/ONBOARDING.md: token setup and tier comparison.
- docs/CONFIGURATION.md: every environment variable.
- The Logs page and /api/logs: backend ring buffer.
- For platform questions about Gitee itself: gitee.com help and the
  platform's open-source communities.

You now have the complete manual, examples, and troubleshooting guidance.
Start with the radar question and follow the data - the rest of the Chinese
open-source world opens up from there.
