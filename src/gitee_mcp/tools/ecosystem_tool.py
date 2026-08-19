"""gitee_ecosystem portmanteau - graph, mirror compare, weekly digest, RSS feed (F7/F9/F10/F14)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from .. import ecosystem, feed
from ..errors import READ_ONLY
from ..server_state import mcp


@mcp.tool(annotations=READ_ONLY, version="0.2.0")
async def gitee_ecosystem(
    operation: Annotated[
        Literal["graph", "mirror", "digest", "feed"],
        Field(
            description=(
                "Operation: 'graph' maps orgs, repos and fork relationships "
                "(scope=seeds|watchlist); 'mirror' compares a repo against its "
                "GitHub twin; 'digest' builds a weekly 'who's rising' narrative "
                "from radar history; 'feed' returns the RSS feed XML."
            )
        ),
    ],
    owner: Annotated[str, Field(description="Repo owner (mirror only).")] = "",
    repo: Annotated[str, Field(description="Repo name (mirror only).")] = "",
    scope: Annotated[
        Literal["seeds", "watchlist"],
        Field(description="Which repos to include in the graph."),
    ] = "seeds",
    days: Annotated[int, Field(description="Digest lookback window in days.", ge=1, le=30)] = 7,
    ctx: Context | None = None,
) -> dict:
    """Chinese-OSS ecosystem intelligence - graph, GitHub mirror comparison, weekly digest, RSS.

    [RATIONALE]
    The radar answers "what is humming now"; these operations answer "what
    is changing" (digest), "who relates to whom" (graph), "where is the
    real community" (mirror) and "how do I subscribe" (feed).

    ## Return Format
    {"success": bool, "operation": str, ...operation-specific fields}

    ## Examples
    gitee_ecosystem(operation="graph")
    gitee_ecosystem(operation="graph", scope="watchlist")
    gitee_ecosystem(operation="mirror", owner="dromara", repo="hutool")
    gitee_ecosystem(operation="digest", days=7)
    gitee_ecosystem(operation="feed")
    """
    if operation == "graph":
        result = ecosystem.build_graph(scope=scope)
        return {
            "success": True,
            "operation": operation,
            "scope": result["scope"],
            "nodes": result["nodes"],
            "edges": result["edges"],
            "counts": result["counts"],
            "note": result["note"],
            "message": f"Graph: {result['counts']['nodes']} nodes, {result['counts']['edges']} edges",
        }
    if operation == "mirror":
        owner = owner.strip("/")
        repo = repo.strip("/")
        if not owner or not repo:
            return {
                "success": False,
                "operation": operation,
                "error": "owner and repo are required for mirror",
                "error_type": "validation",
                "message": "owner and repo are required for mirror",
            }
        result = ecosystem.mirror_compare(owner, repo)
        return {"success": result.get("success", False), "operation": operation, **result}
    if operation == "digest":
        result = ecosystem.weekly_digest(days=days)
        return {
            "success": True,
            "operation": operation,
            "days": result["days"],
            "narrative": result["narrative"],
            "movers": result["movers"],
            "polished": result["polished"],
            "source": result["source"],
            "message": (
                f"Weekly digest ({result['days']}d) with {len(result['movers'])} movers"
                + (" (LLM-polished)" if result["polished"] else "")
            ),
        }
    # feed
    return {
        "success": True,
        "operation": operation,
        "feed_xml": feed.build_feed(),
        "content_type": "application/rss+xml",
        "message": "RSS 2.0 feed of the humming radar",
    }
