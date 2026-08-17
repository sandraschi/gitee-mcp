# Onboarding - gitee-mcp

## What this is for

gitee-mcp is a bridge to **Gitee** (gitee.com), China's largest open-source
platform - the home of OpenHarmony, dromara/hutool, macrozheng/mall and much
of China's OSS ecosystem. The bridge shows what is humming on Gitee (live
activity radar), pulls repository intel (README, languages, commits, files),
searches users and repos, and translates Chinese descriptions to English
using your local LLM. It does **not** push code, open issues or create
repos.

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | **No for anonymous tier.** Optional: Gitee account for a free token |
| Free tier? | Yes - anonymous tier (~60 requests/hour), token tier free |
| Credit card required? | **No** |
| Ongoing cost? | Free (Ollama translation is local; no cloud API used) |
| Who bills? | No one |

## Prerequisites outside this repo

- Nothing for anonymous mode.
- Optional Gitee account: https://gitee.com/signup
- Optional Ollama for full translation: `winget install Ollama.Ollama`, then
  `ollama pull qwen2.5:7b`

## First-timer setup steps

1. (Optional) Create a Gitee account at https://gitee.com/signup - free.
2. (Optional) Create a personal access token:
   https://gitee.com/profile/personal_access_tokens/new
   - Scope: `projects` is enough (read operations).
3. Copy `.env.example` to `.env` and set:
   ```
   GITEE_TOKEN=your_token_here
   ```
4. Restart the server (Option A/C: restart Claude Desktop; Option D: close
   and reopen the start.bat window).
5. (Optional) Install Ollama for full translations:
   ```
   winget install Ollama.Ollama
   ollama pull qwen2.5:7b
   ```

## Pitfalls

- **Anonymous rate limit**: ~60 requests/hour. The server caches responses
  for 10 minutes, so interactive use is fine. A token removes the pain.
- **Repo search silently empty without token**: Gitee's API returns an empty
  list for anonymous repo search. gitee-mcp refuses to show that as a real
  result - it tells you a token is needed instead.
- **Trending page is not scrapable**: Gitee's explore/trending pages block
  non-browser clients (verified HTTP 405 anti-bot challenge). The radar is
  computed from real repo data, not scraped - read docs/ARCHITECTURE.md for
  the methodology.
- **Translation quality**: needs Ollama running. Without it you get a
  dictionary gloss with a visible "partial gloss" marker - never a fake
  translation.
- **Gitee timestamps** are +08:00 (China Standard Time).

## Sanity check

- Settings page in the webapp shows "Token configured - full tier", or
  call `gitee_translate(operation="status")` for LLM health.
- One dry-run tool call:
  `gitee_explore(operation="humming", limit=5)` returns real repos.
- Health endpoint: `GET http://127.0.0.1:11161/api/health` shows
  `"configured": true` when the token is set.

## Declared doubles

- **Anonymous tier is real data, not a mock**: the radar, repo intel and
  user search work live without a token, at a lower rate limit. No sample
  data is ever injected.
- **Gloss fallback**: when Ollama is down, `gitee_translate` returns
  `translated: false` with a dictionary gloss - explicitly flagged, never
  presented as a real translation.
- **Empty repo search without token**: returns an `auth_required` error,
  not fake results.
