# Installing gitee-mcp

> **First time?** Complete [docs/ONBOARDING.md](docs/ONBOARDING.md) before
> expecting the full tier - a free Gitee token unlocks repo search. The
> anonymous tier works immediately with no account at all.

## Prerequisites

Install these if you don't have them already:

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop | Required host (or any MCP client) | [download](https://claude.ai/download) |
| Python + uv | Run server (Option C/D only) | `winget install astral-sh.uv` |
| Node.js | mcpb CLI (Option B only) | `winget install OpenJS.NodeJS` |
| Git | Clone repo (Option C/D only) | `winget install Git.Git` |

> Windows: all installs via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/).
> macOS: `brew install` equivalents. Linux: distro package manager.

## Option A - Drag and Drop (Recommended)

1. Go to [Releases](https://github.com/sandraschi/gitee-mcp/releases/latest)
2. Download `gitee-mcp-v0.1.0.mcpb`
3. Open Claude Desktop -> drag the file onto the window
   *Or*: Settings -> MCP Servers -> Install from file

## Option B - mcpb CLI

```bash
# Requires Node.js (see Prerequisites)
npx @anthropic-ai/mcpb install https://github.com/sandraschi/gitee-mcp
```

## Option C - Manual Configuration

1. Clone: `git clone https://github.com/sandraschi/gitee-mcp`
2. Install deps: `cd gitee-mcp && uv sync`
3. Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "gitee-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\gitee-mcp", "run", "python", "-m", "gitee_mcp.server"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

Config file location:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

4. Restart Claude Desktop

## Option D - Webapp + full stack

For the dashboard (Trending radar, Search, Chat, Settings, Logs):

1. Clone and `cd gitee-mcp`
2. Copy `.env.example` to `.env` and optionally add `GITEE_TOKEN`
3. Double-click `start.bat` (installs uv/node/bun automatically on a naked PC)
4. Open http://127.0.0.1:11162

## Optional: local LLM for translation

```powershell
winget install Ollama.Ollama
ollama pull qwen2.5:7b
```

Without an LLM, translations fall back to a dictionary gloss (honestly flagged).

## Verify Installation

After installing, open Claude Desktop and type:

> "What is humming on Gitee right now?"

You should see a ranked list of Gitee repos with stars, forks, languages and
recent commit activity.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
