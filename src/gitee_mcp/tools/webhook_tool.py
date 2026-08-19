"""gitee_webhook portmanteau - inbound Gitee webhook events (push, star, fork...)."""

from __future__ import annotations

import json
from typing import Annotated, Literal
from uuid import uuid4

from fastmcp import Context
from pydantic import Field

from ..config import DATA_DIR
from ..errors import MUTATING
from ..server_state import mcp

_WEBHOOK_DB = DATA_DIR / "webhook_events.jsonl"


def append_event(payload: dict, headers: dict | None = None) -> str:
    """Persist one webhook event and return its id. Used by the REST receiver."""
    event_id = str(uuid4())
    _WEBHOOK_DB.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "id": event_id,
        "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "event": (headers or {}).get("x-gitee-event", "unknown"),
        "payload": payload,
    }
    try:
        with _WEBHOOK_DB.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return event_id


def list_events(limit: int = 20) -> list[dict]:
    if not _WEBHOOK_DB.exists():
        return []
    rows = []
    try:
        with _WEBHOOK_DB.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows[-max(limit, 1) :]


def clear_events() -> int:
    count = 0
    if _WEBHOOK_DB.exists():
        try:
            count = len(list_events(10_000))
            _WEBHOOK_DB.unlink()
        except OSError:
            pass
    return count


@mcp.tool(annotations=MUTATING, version="0.1.0")
async def gitee_webhook(
    operation: Annotated[
        Literal["list", "clear"],
        Field(description="Operation: 'list' recent inbound webhook events, 'clear' wipes them."),
    ],
    limit: Annotated[int, Field(description="Max events (1-50).", ge=1, le=50)] = 20,
    ctx: Context | None = None,
) -> dict:
    """Inspect inbound Gitee webhook events (push, star, fork, pull_request...).

    [RATIONALE]
    Gitee pushes events to POST /api/webhooks/gitee when a repo webhook is
    configured; this tool surfaces the captured feed so agents can react
    to CI pushes, stars and forks.

    ## Return Format
    {"success": bool, "operation": str, "events": [...], "count": int}

    ## Examples
    gitee_webhook(operation="list", limit=10)
    gitee_webhook(operation="clear")
    """
    if operation == "clear":
        cleared = clear_events()
        return {
            "success": True,
            "operation": operation,
            "count": cleared,
            "message": f"Cleared {cleared} webhook events",
        }
    events = list_events(limit)
    slim = [
        {
            "id": e.get("id"),
            "ts": e.get("ts"),
            "event": e.get("event"),
            "summary": _summarize(e),
        }
        for e in events
    ]
    return {
        "success": True,
        "operation": operation,
        "events": slim,
        "count": len(slim),
        "message": f"{len(slim)} webhook event(s) in the feed",
    }


def _summarize(event: dict) -> str:
    payload = event.get("payload") or {}
    etype = event.get("event", "")
    if etype == "Push Hook":
        repo = ((payload.get("repository") or {}).get("full_name")) or ""
        branch = ((payload.get("ref") or "").rsplit("/", 1)[-1]) or "?"
        commits = payload.get("total_commits_count") or len(payload.get("commits") or [])
        user = ((payload.get("user_name")) or (payload.get("pusher") or {}).get("name")) or "?"
        return f"{user} pushed {commits} commit(s) to {repo}@{branch}"
    if etype in ("Star Hook", "Watch Hook"):
        repo = ((payload.get("repository") or {}).get("full_name")) or ""
        user = (payload.get("starred_by") or {}).get("login") or "?"
        return f"{user} starred {repo}"
    if etype == "Fork Hook":
        repo = ((payload.get("repository") or {}).get("full_name")) or ""
        fork = ((payload.get("forked_repository") or {}).get("full_name")) or "?"
        return f"{repo} was forked to {fork}"
    repo = ((payload.get("repository") or {}).get("full_name")) or ""
    return f"{etype} on {repo or 'unknown repo'}"
