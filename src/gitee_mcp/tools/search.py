"""gitee_search portmanteau - user search (anonymous) and repo search (token tier)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from ..client import GiteeError, get_client
from ..server_state import mcp


@mcp.tool(version="0.1.0")
async def gitee_search(
    operation: Annotated[
        Literal["users", "repos", "user_repos"],
        Field(
            description=(
                "Operation: 'users' searches Gitee users by login/name (works "
                "anonymously); 'repos' searches repositories (requires GITEE_TOKEN, "
                "returns an actionable error otherwise); 'user_repos' lists a "
                "user's public repos (anonymous)."
            )
        ),
    ],
    query: Annotated[
        str, Field(description="Search term (user login/name, or repo keyword for 'repos').")
    ],
    limit: Annotated[int, Field(description="Max results (1-100).", ge=1, le=100)] = 10,
    sort: Annotated[
        Literal["stargazers_count", "forks_count", "updated", "pushed"],
        Field(description="Sort key for repo search (token tier)."),
    ] = "stargazers_count",
    login: Annotated[str, Field(description="Gitee login for 'user_repos'.")] = "",
    ctx: Context | None = None,
) -> dict:
    """Search Gitee users and repositories, or list a user's public repos.

    [RATIONALE]
    Search is one domain with three surfaces (users, repos, user repos);
    one tool with an operation discriminator keeps discovery compact.

    ## Return Format
    {"success": bool, "operation": str, "data": [...], "count": int}

    ## Examples
    gitee_search(operation="users", query="sandra")
    gitee_search(operation="repos", query="fastmcp", limit=10)
    gitee_search(operation="user_repos", login="macrozheng", limit=20)
    """
    client = get_client()
    try:
        if operation == "users":
            data = client.search_users(query, limit)
            slim = [
                {
                    "login": u.get("login", ""),
                    "name": u.get("name") or u.get("login", ""),
                    "html_url": f"https://gitee.com/{u.get('login', '')}",
                    "remark": u.get("remark") or "",
                }
                for u in data
            ]
            return {"success": True, "operation": operation, "data": slim, "count": len(slim)}
        if operation == "repos":
            _, items = client.search_repositories(query, sort=sort, per_page=limit)
            slim = [
                {
                    "full_name": r.get("full_name", ""),
                    "html_url": (r.get("html_url") or "").replace(".git", ""),
                    "description": r.get("description") or "",
                    "language": r.get("language"),
                    "stargazers_count": r.get("stargazers_count") or 0,
                    "forks_count": r.get("forks_count") or 0,
                    "pushed_at": r.get("pushed_at"),
                }
                for r in items
            ]
            return {"success": True, "operation": operation, "data": slim, "count": len(slim)}
        if operation == "user_repos":
            if not login:
                return {
                    "success": False,
                    "operation": operation,
                    "error": "login required for user_repos",
                    "error_type": "validation",
                }
            data = client.user_repos(login, limit)
            slim = [
                {
                    "full_name": r.get("full_name", ""),
                    "html_url": (r.get("html_url") or "").replace(".git", ""),
                    "description": r.get("description") or "",
                    "language": r.get("language"),
                    "stargazers_count": r.get("stargazers_count") or 0,
                    "forks_count": r.get("forks_count") or 0,
                    "pushed_at": r.get("pushed_at"),
                }
                for r in data
            ]
            return {"success": True, "operation": operation, "data": slim, "count": len(slim)}
        return {
            "success": False,
            "operation": operation,
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
                ["Set GITEE_TOKEN (free, no CC) at gitee.com/profile/personal_access_tokens/new."]
                if exc.error_type == "auth_required"
                else []
            ),
        }
