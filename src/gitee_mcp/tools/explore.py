"""gitee_explore portmanteau - the "what's humming" radar and discovery ops."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from ..client import GiteeError, get_client
from ..errors import READ_ONLY, error_response
from ..radar import humming_radar
from ..server_state import mcp

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "data": {
            "type": "object",
            "properties": {
                "repos": {"type": "array"},
                "total": {"type": "integer"},
                "dead_seeds": {"type": "array"},
                "throttled_seeds": {"type": "array"},
                "tier": {"type": "string"},
                "generated_at": {"type": "string"},
            },
        },
        "error": {"type": "string"},
        "error_type": {"type": "string"},
        "suggestions": {"type": "array"},
    },
}


@mcp.tool(annotations=READ_ONLY, output_schema=_OUTPUT_SCHEMA, version="0.2.0")
async def gitee_explore(
    operation: Annotated[
        Literal[
            "humming",
            "momentum",
            "top_starred",
            "top_forked",
            "recommended",
            "refresh",
        ],
        Field(
            description=(
                "Operation: 'humming' derives a ranked live feed from real "
                "commit/star/forks data of popular seed repos (works anonymously) "
                "and includes momentum deltas; 'momentum' ranks the same repos by "
                "activity change over ~7 days (needs history, see note); "
                "'top_starred' / 'top_forked' query repo search sorted by stars or "
                "forks (requires GITEE_TOKEN); 'recommended' returns the seed list; "
                "'refresh' re-verifies seed repos and drops dead ones."
            )
        ),
    ] = "humming",
    limit: Annotated[int, Field(description="Max repos to return (1-50).", ge=1, le=50)] = 20,
    language: Annotated[
        str, Field(description="Filter by main language, e.g. 'Python', 'Java' (empty = all).")
    ] = "",
    translate: Annotated[
        bool, Field(description="Translate Chinese descriptions to English via local LLM.")
    ] = False,
    ctx: Context | None = None,
) -> dict:
    """Explore what is humming on Gitee - live ranked activity radar, top-starred and top-forked discovery.

    [RATIONALE]
    Gitee has no public trending API (the explore pages are behind an
    anti-bot challenge). One tool consolidates the anonymous radar, the
    token-tier sorted searches, and seed maintenance instead of four
    separate discovery tools.

    ## Return Format
    {"success": bool, "message": str, "data": {"repos": [...], "total": int,
     "dead_seeds": [...], "tier": str, "generated_at": str}}
    Each repo: {full_name, owner, description, translation, language,
    stargazers_count, forks_count, pushed_at, activity_score, recent_commits}

    ## Examples
    gitee_explore(operation="humming", limit=10)
    gitee_explore(operation="humming", language="Python", translate=True)
    gitee_explore(operation="momentum", limit=10)
    gitee_explore(operation="top_starred", limit=15)
    """
    try:
        if operation == "humming":
            result = humming_radar(limit=limit, language=language, translate=translate)
        elif operation == "momentum":
            from ..history import top_movers

            movers = top_movers(days=7, limit=limit)
            result = {
                "success": True,
                "message": (
                    f"Top {len(movers)} movers by activity delta (7d) - "
                    "first run needs history to build baselines"
                    if movers
                    else "No history yet - run humming over separate days to build momentum baselines"
                ),
                "data": {
                    "movers": movers,
                    "total": len(movers),
                    "note": "Deltas from gitee-mcp radar history (our observations, not Gitee's full history).",
                },
            }
        elif operation in ("top_starred", "top_forked"):
            client = get_client()
            sort = "stargazers_count" if operation == "top_starred" else "forks_count"
            _, items = client.search_repositories(
                query="stars:>10" if operation == "top_starred" else "forks:>10",
                sort=sort,
                per_page=min(limit, 50),
            )
            result = {
                "success": True,
                "message": f"{operation} returned {len(items)} repos",
                "data": {
                    "repos": [
                        {
                            "full_name": r.get("full_name", ""),
                            "owner": ((r.get("owner") or {}).get("login") or ""),
                            "html_url": (r.get("html_url") or "").replace(".git", ""),
                            "description": r.get("description") or "",
                            "language": r.get("language"),
                            "stargazers_count": r.get("stargazers_count") or 0,
                            "forks_count": r.get("forks_count") or 0,
                            "pushed_at": r.get("pushed_at"),
                        }
                        for r in items
                    ],
                    "total": len(items),
                    "tier": "token",
                },
            }
        elif operation == "recommended":
            from ..config import settings

            result = {
                "success": True,
                "message": f"{len(settings.seed_repos)} seed repos configured",
                "data": {"repos": settings.seed_repos, "total": len(settings.seed_repos)},
            }
        else:  # refresh
            client = get_client()
            alive, dead = [], []
            for seed in client.cfg.seed_repos:
                if "/" not in seed:
                    continue
                owner, repo = seed.split("/", 1)
                try:
                    client.repo_details(owner.strip(), repo.strip())
                    alive.append(seed)
                except GiteeError:
                    dead.append(seed)
            result = {
                "success": True,
                "message": f"Seeds verified: {len(alive)} alive, {len(dead)} dead",
                "data": {"alive": alive, "dead": dead},
            }
        return result
    except GiteeError as exc:
        return error_response(
            exc,
            error_type=exc.error_type,
            suggestions=(
                [
                    "Set GITEE_TOKEN (free) for the full tier.",
                    "Run with translate=False to skip LLM translation.",
                ]
                if exc.error_type == "auth_required"
                else ["Check network connectivity to gitee.com."]
            ),
            operation=operation,
        )
