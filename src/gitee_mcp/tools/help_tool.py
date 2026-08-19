"""gitee_help - discovery and configuration documentation."""

from __future__ import annotations

from fastmcp import Context

from ..errors import READ_ONLY
from ..server_state import mcp

_HELP = """# Gitee MCP

Bridge to Gitee (gitee.com), China's largest GitHub-style platform. See what
is humming in the Chinese open-source world, search users and repos, pull
repo intel, and translate Chinese descriptions to English.

## Tools

- `gitee_explore` - humming radar (anonymous), momentum deltas, top-starred/top-forked (token), seeds
- `gitee_repo` - details, readme, languages, commits, contents, branches, stack, releases, star history
- `gitee_search` - users (anonymous), repos (token, cross-lingual expansion), user repos
- `gitee_translate` - zh -> en via local LLM, detect, provider status, culture explain
- `gitee_webhook` - inbound webhook event feed + grouped digest
- `gitee_watchlist` - persistent watchlist with change detection + auto-follow thresholds
- `gitee_ecosystem` - ecosystem graph, GitHub mirror comparison, weekly digest, RSS feed
- `gitee_corpus` - README keyword corpus search (BM25 FTS5, RAG-lite)
- `show_gitee_humming_card` / `show_gitee_status_card` - rich in-chat cards
- `gitee_shutdown` - graceful self-termination

## Tiers

| Surface | Anonymous | With GITEE_TOKEN |
|---|---|---|
| Repo details / readme / languages / commits / branches / contents | yes | yes |
| User search / user repos | yes | yes |
| Humming radar (seed-based, real data) | yes | yes |
| Repo search / top-starred / stargazers | no | yes |

## Configuration

- GITEE_TOKEN - optional, free: gitee.com/profile/personal_access_tokens/new
- GITEE_LLM_BASE_URL - local LLM (default http://127.0.0.1:11434/v1)
- GITEE_LLM_MODEL - translation model (default qwen2.5:7b)
- GITEE_SEED_REPOS - comma-separated owner/repo list for the radar
- GITEE_WEBHOOK_SECRET - optional webhook receiver secret

## Notes

- Anonymous tier is rate-limited to ~60 requests/hour - responses are cached.
- Repo descriptions are often Chinese; pass translate=True or call
  gitee_translate to gloss them via the local LLM.
"""


@mcp.tool(annotations=READ_ONLY, version="0.1.0")
async def gitee_help(ctx: Context | None = None) -> dict:
    """Gitee MCP help - tools, tiers, configuration and tips.

    ## Return Format
    {"success": bool, "help": str}

    ## Examples
    gitee_help()
    """
    return {"success": True, "help": _HELP}
