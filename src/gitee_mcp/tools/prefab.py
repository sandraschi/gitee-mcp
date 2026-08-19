"""Prefab UI cards - required in-chat surfaces for list/status tools."""

from __future__ import annotations

from fastmcp import Context
from fastmcp.tools import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import (
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Div,
    Heading,
    Row,
    Text,
)

from ..client import get_client
from ..config import settings
from ..errors import READ_ONLY
from ..radar import humming_radar
from ..server_state import mcp
from ..translate import translator


def _kv(label: str, value: str) -> Row:
    """Key/value row - prefab Row is a layout container, so pair Texts."""
    return Row(
        justify="between",
        children=[
            Text(label, css_class="text-zinc-400"),
            Text(value, css_class="font-semibold"),
        ],
    )


@mcp.tool(app=True, annotations=READ_ONLY, version="0.1.0")
async def show_gitee_humming_card(
    limit: int = 10,
    translate: bool = False,
    ctx: Context | None = None,
) -> ToolResult:
    """Show what is humming on Gitee right now as a rich in-chat card.

    [RATIONALE]
    Status/list tools MUST ship a Prefab surface per fleet SOTA - this card
    renders the radar ranking in chat without the agent reading raw JSON.

    ## Return Format
    ToolResult with content (plain text fallback) + structured PrefabApp card.

    ## Examples
    show_gitee_humming_card(limit=5)
    """
    result = humming_radar(limit=limit, translate=translate)
    repos = result.get("data", {}).get("repos", [])
    lines = []
    with PrefabApp(title="Gitee Humming Radar") as app:
        Heading("What is humming on Gitee")
        Text(result.get("message", ""))
        for repo in repos[:10]:
            name = repo.get("full_name", "")
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            lang = repo.get("language") or "-"
            desc = repo.get("description") or "(no description)"
            if repo.get("translation"):
                desc = f"{desc} | {repo['translation']}"
            with Card(css_class="mb-2"):
                with CardHeader():
                    CardTitle(name)
                with CardContent():
                    Text(desc)
                    _kv("Stars", str(stars))
                    _kv("Forks", str(forks))
                    _kv("Language", str(lang))
                    _kv("Activity", str(repo.get("activity_score", 0)))
            lines.append(f"- **{name}** ({lang}, {stars} stars, {forks} forks): {desc}")
    plain = f"{result.get('message', '')}\n" + "\n".join(lines)
    return ToolResult(content=plain, structured_content=app)


@mcp.tool(app=True, annotations=READ_ONLY, version="0.1.0")
async def show_gitee_status_card(ctx: Context | None = None) -> ToolResult:
    """Show gitee-mcp configuration status as a rich in-chat card.

    [RATIONALE]
    Status tools MUST ship a Prefab surface - one call shows tier, token
    state, LLM provider health and rate-limit headroom at a glance.

    ## Return Format
    ToolResult with content (plain text fallback) + structured PrefabApp card.

    ## Examples
    show_gitee_status_card()
    """
    client = get_client()
    snapshot = client.status_snapshot()
    llm = translator.provider_health()
    with PrefabApp(title="Gitee MCP Status") as app:
        Heading("gitee-mcp")
        _kv("Tier", "Token (full)" if snapshot["configured"] else "Anonymous (rate-limited)")
        _kv(
            "Rate limit",
            (
                f"{snapshot['rate_limit_remaining']}/{snapshot['rate_limit_total']} remaining"
                if snapshot["rate_limit_remaining"] is not None
                else "unknown"
            ),
        )
        _kv(
            "LLM provider", "Ollama reachable" if llm["available"] else "Not reachable (gloss mode)"
        )
        _kv("LLM model", llm["model"])
        _kv("Seed repos", str(len(settings.seed_repos)))
        Div()
        Text(
            "Anonymous tier works out of the box. Set GITEE_TOKEN for repo search and higher limits."
        )
    plain = (
        f"Tier: {snapshot['tier']} | Rate limit: {snapshot['rate_limit_remaining']}/{snapshot['rate_limit_total']} | "
        f"LLM: {'reachable' if llm['available'] else 'not reachable (gloss mode)'} | "
        f"Model: {llm['model']} | Seeds: {len(settings.seed_repos)}"
    )
    return ToolResult(content=plain, structured_content=app)
