"""gitee_watchlist portmanteau - persistent repo watchlist with change detection (F5)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from ..errors import MUTATING
from ..server_state import mcp
from ..watchlist import add, check, list_entries, remove

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "operation": {"type": "string"},
        "message": {"type": "string"},
        "entries": {"type": "array"},
        "count": {"type": "integer"},
        "error": {"type": "string"},
        "error_type": {"type": "string"},
    },
}


@mcp.tool(annotations=MUTATING, output_schema=_OUTPUT_SCHEMA, version="0.2.0")
async def gitee_watchlist(
    operation: Annotated[
        Literal["add", "remove", "list", "check"],
        Field(
            description=(
                "Operation: 'add' watches a repo (optional min_activity threshold "
                "for auto-follow alerts); 'remove' stops watching; 'list' shows "
                "watched repos; 'check' diffs each watched repo's recent commits "
                "against the last check and reports new activity."
            )
        ),
    ],
    full_name: Annotated[str, Field(description="Repo as owner/repo (e.g. dromara/hutool).")] = "",
    min_activity: Annotated[
        float | None,
        Field(description="Auto-follow alert threshold on activity_score (optional)."),
    ] = None,
    ctx: Context | None = None,
) -> dict:
    """Watch Gitee repos persistently and detect what changed since the last check.

    [RATIONALE]
    One persistent watchlist turns the radar into a notification feed: add
    repos you care about, check periodically, and see exactly what changed
    (new commits, optional activity-threshold crossings) instead of
    re-scanning everything.

    ## Return Format
    {"success": bool, "operation": str, "message": str,
    "entries": [...], "count": int}

    ## Examples
    gitee_watchlist(operation="add", full_name="dromara/hutool")
    gitee_watchlist(operation="add", full_name="macrozheng/mall", min_activity=8.0)
    gitee_watchlist(operation="list")
    gitee_watchlist(operation="check")
    gitee_watchlist(operation="remove", full_name="dromara/hutool")
    """
    if operation == "add":
        full_name = (full_name or "").strip().strip("/")
        if not full_name or "/" not in full_name:
            return {
                "success": False,
                "operation": operation,
                "error": "full_name must be owner/repo",
                "error_type": "validation",
                "message": "full_name must be owner/repo",
            }
        entry = add(full_name, min_activity=min_activity)
        return {
            "success": True,
            "operation": operation,
            "message": f"Watching {entry.full_name}"
            + (f" (min_activity={min_activity})" if min_activity is not None else ""),
            "entries": [entry.full_name],
            "count": 1,
        }
    if operation == "remove":
        removed = remove(full_name)
        return {
            "success": True,
            "operation": operation,
            "message": f"Stopped watching {full_name}"
            if removed
            else f"{full_name} not in watchlist",
            "count": 1 if removed else 0,
        }
    if operation == "list":
        entries = list_entries()
        slim = [
            {
                "full_name": e.full_name,
                "min_activity": e.min_activity,
                "added_at": e.added_at,
            }
            for e in entries
        ]
        return {
            "success": True,
            "operation": operation,
            "entries": slim,
            "count": len(slim),
            "message": f"{len(slim)} repo(s) watched",
        }
    # check
    report = check()
    return {
        "success": True,
        "operation": operation,
        "message": (
            f"{report['count']} repo(s) checked - "
            + ("changes found" if report["changed_any"] else "nothing new")
        ),
        "entries": report["entries"],
        "count": report["count"],
    }
