"""gitee_webhook portmanteau - inbound Gitee webhook events (push, star, fork...)."""

from __future__ import annotations

import json
import time
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


def digest_events(since_hours: int = 24) -> dict:
    """Group the event feed by repo and event type into a digest summary."""
    since_hours = max(1, min(int(since_hours), 168))
    events = list_events(200)
    since_ts = time.time() - since_hours * 3600
    recent = []
    for e in events:
        try:
            ts = time.mktime(time.strptime(e.get("ts", ""), "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            continue
        if ts >= since_ts:
            recent.append(e)
    by_repo: dict[str, dict] = {}
    for e in recent:
        payload = e.get("payload") or {}
        repo = ((payload.get("repository") or {}).get("full_name")) or "unknown"
        group = by_repo.setdefault(repo, {"count": 0, "summary": []})
        group["count"] += 1
        group["summary"].append(_summarize(e))
    return {
        "success": True,
        "since_hours": since_hours,
        "digest": [
            {"repo": repo, "count": group["count"], "summary": group["summary"][:20]}
            for repo, group in sorted(by_repo.items(), key=lambda kv: -kv[1]["count"])
        ],
        "event_count": len(recent),
        "message": (
            f"{len(recent)} event(s) in the last {since_hours}h across {len(by_repo)} repo(s)"
        ),
    }


@mcp.tool(annotations=MUTATING, version="0.2.0")
async def gitee_webhook(
    operation: Annotated[
        Literal["list", "clear", "digest"],
        Field(
            description=(
                "Operation: 'list' recent inbound webhook events, 'clear' wipes "
                "them, 'digest' groups events by repo and event type into a "
                "daily-style summary (since_hours lookback)."
            )
        ),
    ],
    limit: Annotated[int, Field(description="Max events (1-50).", ge=1, le=50)] = 20,
    since_hours: Annotated[int, Field(description="Digest lookback in hours.", ge=1, le=168)] = 24,
    ctx: Context | None = None,
) -> dict:
    """Inspect inbound Gitee webhook events or read a grouped daily digest.

    [RATIONALE]
    Gitee pushes events to POST /api/webhooks/gitee when a repo webhook is
    configured; this tool surfaces the captured feed so agents can react
    to CI pushes, stars and forks - and 'digest' turns the raw feed into a
    "what happened on my repos" report.

    ## Return Format
    {"success": bool, "operation": str, "events": [...], "count": int}

    ## Examples
    gitee_webhook(operation="list", limit=10)
    gitee_webhook(operation="digest", since_hours=24)
    gitee_webhook(operation="clear")
    """
    if operation == "digest":
        result = digest_events(since_hours=since_hours)
        return {
            "success": True,
            "operation": operation,
            "since_hours": result["since_hours"],
            "digest": result["digest"],
            "event_count": result["event_count"],
            "message": result["message"],
        }
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
