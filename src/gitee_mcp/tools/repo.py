"""gitee_repo portmanteau - repository intel (details, readme, languages, commits, contents, branches)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from ..client import GiteeError, get_client
from ..errors import READ_ONLY, error_response
from ..server_state import mcp

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "operation": {"type": "string"},
        "message": {"type": "string"},
        "data": {},
        "error": {"type": "string"},
        "error_type": {"type": "string"},
        "suggestions": {"type": "array"},
    },
}

_REPO_OPS = (
    "details",
    "readme",
    "languages",
    "commits",
    "contents",
    "branches",
    "stack",
    "releases",
    "star_history",
)


@mcp.tool(annotations=READ_ONLY, output_schema=_OUTPUT_SCHEMA, version="0.2.0")
async def gitee_repo(
    operation: Annotated[
        Literal[
            "details",
            "readme",
            "languages",
            "commits",
            "contents",
            "branches",
            "stack",
            "releases",
            "star_history",
        ],
        Field(
            description=(
                "Operation: 'details' full metadata; 'readme' decoded README markdown "
                "(None when absent; also indexed into the local corpus); 'languages' "
                "byte/percent breakdown; 'commits' recent commit list; 'contents' "
                "file/dir listing for a path; 'branches' branch list; 'stack' "
                "Chinese-OSS tech-stack fingerprint; 'releases' latest releases with "
                "an English summary; 'star_history' observed stars/forks/activity "
                "series from gitee-mcp radar history."
            )
        ),
    ],
    owner: Annotated[str, Field(description="Repo owner (user or org path on gitee.com).")],
    repo: Annotated[str, Field(description="Repo name.")],
    path: Annotated[str, Field(description="Path within the repo (contents only).")] = "",
    limit: Annotated[int, Field(description="Max rows (commits 1-100).", ge=1, le=100)] = 10,
    ctx: Context | None = None,
) -> dict:
    """Gitee repository intel - metadata, README, languages, commits, file tree and branches.

    [RATIONALE]
    A single repo has many read surfaces; one portmanteau keeps the tool
    registry small while exposing all of them with a shared owner/repo
    contract.

    ## Return Format
    {"success": bool, "operation": str, "data": {...}} on success.
    On failure: {"success": false, "error": str, "error_type": str,
    "suggestions": [...]}

    ## Examples
    gitee_repo(operation="details", owner="dromara", repo="hutool")
    gitee_repo(operation="readme", owner="apache", repo="dubbo")
    gitee_repo(operation="commits", owner="macrozheng", repo="mall", limit=5)
    gitee_repo(operation="contents", owner="snailclimb", repo="JavaGuide", path="docs")
    gitee_repo(operation="stack", owner="dromara", repo="hutool")
    gitee_repo(operation="releases", owner="apache", repo="skywalking")
    gitee_repo(operation="star_history", owner="macrozheng", repo="mall")
    """
    client = get_client()
    owner = owner.strip("/")
    repo_name = repo.strip("/")
    try:
        if operation == "details":
            data = client.repo_details(owner, repo_name)
            data["html_url"] = (data.get("html_url") or "").replace(".git", "")
            data.pop("assigner", None)
            data.pop("members", None)
            data.pop("programs", None)
            data.pop("enterprise", None)
            return {
                "success": True,
                "operation": operation,
                "data": data,
                "message": f"Fetched {owner}/{repo_name} details",
            }
        if operation == "readme":
            readme = client.repo_readme(owner, repo_name)
            if readme is None:
                return {
                    "success": True,
                    "operation": operation,
                    "data": None,
                    "message": f"{owner}/{repo_name} has no README",
                }
            max_chars = 60000
            # Local corpus auto-index (best-effort, never blocks the response).
            from ..corpus import ingest as _ingest

            _ingest(f"{owner}/{repo_name}", readme)
            return {
                "success": True,
                "operation": operation,
                "data": readme[:max_chars],
                "truncated": len(readme) > max_chars,
                "message": f"README for {owner}/{repo_name} ({len(readme)} chars)",
            }
        if operation == "languages":
            languages = client.repo_languages(owner, repo_name)
            return {
                "success": True,
                "operation": operation,
                "data": languages,
                "message": f"{len(languages)} languages for {owner}/{repo_name}",
            }
        if operation == "commits":
            commits = client.repo_commits(owner, repo_name, limit)
            return {
                "success": True,
                "operation": operation,
                "data": commits,
                "message": f"{len(commits)} recent commits for {owner}/{repo_name}",
            }
        if operation == "contents":
            items = client.repo_contents(owner, repo_name, path)
            return {
                "success": True,
                "operation": operation,
                "data": items,
                "message": f"{len(items)} entries in {owner}/{repo_name}/{path or ''}",
            }
        if operation == "branches":
            branches = [b.get("name") for b in client.repo_branches(owner, repo_name)]
            return {
                "success": True,
                "operation": operation,
                "data": branches,
                "message": f"{len(branches)} branches for {owner}/{repo_name}",
            }
        if operation == "stack":
            from ..stack import fingerprint

            readme = client.repo_readme(owner, repo_name) or ""
            contents = client.repo_contents(owner, repo_name)
            details = client.repo_details(owner, repo_name)
            result = fingerprint(
                details.get("description") or "", readme, [c.get("name", "") for c in contents]
            )
            return {
                "success": True,
                "operation": operation,
                "data": result,
                "message": (f"Stack for {owner}/{repo_name}: {result['dominant'] or 'unknown'}"),
            }
        if operation == "releases":
            from ..release_notes import summarize_latest

            result = summarize_latest(owner, repo_name, limit=min(limit, 5))
            return {
                "success": result.get("success", True),
                "operation": operation,
                "data": {
                    "summary": result.get("summary"),
                    "translated": result.get("translated", False),
                    "releases": result.get("releases", []),
                },
                "message": (
                    f"{len(result.get('releases', []))} release(s) for {owner}/{repo_name}"
                    if result.get("has_releases")
                    else f"{owner}/{repo_name} has no releases on Gitee"
                ),
            }
        if operation == "star_history":
            from ..history import star_history

            series = star_history(f"{owner}/{repo_name}", limit=min(limit, 30))
            return {
                "success": True,
                "operation": operation,
                "data": series,
                "message": (
                    f"{len(series)} observation(s) for {owner}/{repo_name} "
                    "- from gitee-mcp radar history, not Gitee's full history"
                ),
            }
        return {
            "success": False,
            "error": f"unknown operation {operation}",
            "error_type": "validation",
            "message": f"unknown operation {operation}",
        }
    except GiteeError as exc:
        return error_response(
            exc,
            error_type=exc.error_type,
            operation=operation,
            suggestions=(
                ["Check the owner/repo spelling.", "Repos must be public for anonymous access."]
                if exc.error_type == "not_found"
                else [
                    "Set GITEE_TOKEN for higher rate limits.",
                    "Retry after the rate window resets.",
                ]
            ),
        )
