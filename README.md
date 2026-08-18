# gitee-mcp

A bridge to **Gitee** (gitee.com), China's largest GitHub-style platform:
see what is humming in the Chinese open-source world, pull repo intel,
search users and repos, and translate Chinese descriptions to English with
your local LLM.

## What this wraps

**Gitee** is the biggest Chinese-language code hosting platform (12M+
users, home of OpenHarmony, dromara/hutool, macrozheng/mall and much of
China's OSS). Its ecosystem is nearly invisible from Western tooling, and
its API is rate-limited and partially token-gated. gitee-mcp bridges it:
anonymous mode works out of the box, a free token unlocks full search.
See [docs/WRAPPEE.md](docs/WRAPPEE.md) for the full picture.

## What You Can Do

- **Humming radar** - a live, ranked view of what is active on Gitee,
  computed from real commit/star/fork data (Gitee has no public trending
  API; the radar is our transparent methodology, not a simulation).
- **Repo intel** - details, README, language mix, recent commits, file
  tree and branches for any public repo.
- **Search** - users anonymously; repos with a free token.
- **Translation** - Chinese descriptions, issues and commits to English
  via Ollama (dictionary gloss fallback when no local model is running).
- **Webhooks** - receive push/star/fork events and watch the feed.
- **Webapp** - dark-theme dashboard for all of the above (ports 11161/11162).

## Preview

| Dashboard |
|-----------|
| ![Dashboard](docs/screenshots/dashboard.png) |
*Dark-theme dashboard: humming radar hero, KPI cards, onboarding cue.*

## Quick Install

**Option A - drag and drop (Claude Desktop):** download
`gitee-mcp-v0.1.0.mcpb` from
[Releases](https://github.com/sandraschi/gitee-mcp/releases/latest) and
drag it onto Claude Desktop. Works immediately in anonymous mode.

**Option C - manual:**

```bash
git clone https://github.com/sandraschi/gitee-mcp
cd gitee-mcp && uv sync
```

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gitee-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\gitee-mcp", "run", "python", "-m", "gitee_mcp.server"]
    }
  }
}
```

All methods: [INSTALL.md](INSTALL.md).

> **First time?** Complete [docs/ONBOARDING.md](docs/ONBOARDING.md) to
> create a free Gitee token (optional but unlocks repo search).

## Example Prompts

- "What is humming on Gitee right now?"
- "Show me the 10 most active Python repos on Gitee, translated to English."
- "Profile dromara/hutool and summarize its README."
- "Search Gitee for users named macrozheng."
- "Translate this to English: 企业级微服务快速开发框架"

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods (A-D), prerequisites |
| [Onboarding](docs/ONBOARDING.md) | Free Gitee token, tier comparison, pitfalls |
| [Wrapped platform](docs/WRAPPEE.md) | Gitee overview, API quirks, community links |
| [Architecture](docs/ARCHITECTURE.md) | Dual transport, REST surface, caching, ports |
| [Configuration](docs/CONFIGURATION.md) | All env vars |
| [Tool Reference](docs/TOOLS.md) | Every tool and operation |
| [Development](docs/DEVELOPMENT.md) | Dev setup, tests, contributing |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and fixes |

## Requirements

- Python 3.11+ (via `uv`)
- Claude Desktop or any MCP host
- Optional: Ollama (`winget install Ollama.Ollama`, `ollama pull qwen2.5:7b`)
  for translation
- Optional: free Gitee token for repo search

## License

MIT
