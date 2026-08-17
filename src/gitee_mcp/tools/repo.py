"""gitee_repo portmanteau - repository intel (details, readme, languages, commits, contents, branches)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from ..client import GiteeError, get_client
from ..server_state import mcp


@mcp.tool(version="0.1.0")
async def gitee_repo(
    operation: Annotated[
        Literal["details", "readme", "languages", "commits", "contents", "branches"],
        Field(
            description=(
                "Operation: 'details' full metadata; 'readme' decoded README markdown "
                "(None when absent); 'languages' byte/percent breakdown; 'commits' "
                "recent commit list; 'contents' file/dir listing for a path; "
                "'branches' branch list."
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
            return {"success": True, "operation": operation, "data": data}
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
            return {
                "success": True,
                "operation": operation,
                "data": readme[:max_chars],
                "truncated": len(readme) > max_chars,
            }
        if operation == "languages":
            return {
                "success": True,
                "operation": operation,
                "data": client.repo_languages(owner, repo_name),
            }
        if operation == "commits":
            return {
                "success": True,
                "operation": operation,
                "data": client.repo_commits(owner, repo_name, limit),
            }
        if operation == "contents":
            return {
                "success": True,
                "operation": operation,
                "data": client.repo_contents(owner, repo_name, path),
            }
        if operation == "branches":
            return {
                "success": True,
                "operation": operation,
                "data": [b.get("name") for b in client.repo_branches(owner, repo_name)],
            }
        return {
            "success": False,
            "error": f"unknown operation {operation}",
            "error_type": "validation",
        }
    except GiteeError as exc:
        return {
            "success": False,
            "operation": operation,
            "error": exc.message,
            "error_type": exc.error_type,
            "suggestions": (
                ["Check the owner/repo spelling.", "Repos must be public for anonymous access."]
                if exc.error_type == "not_found"
                else [
                    "Set GITEE_TOKEN for higher rate limits.",
                    "Retry after the rate window resets.",
                ]
            ),
        }
