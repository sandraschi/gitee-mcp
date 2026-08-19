"""gitee_corpus portmanteau - README keyword corpus (RAG-lite, F13)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from .. import corpus
from ..client import get_client
from ..errors import MUTATING
from ..server_state import mcp

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "operation": {"type": "string"},
        "message": {"type": "string"},
        "results": {"type": "array"},
        "count": {"type": "integer"},
        "error": {"type": "string"},
        "error_type": {"type": "string"},
    },
}


@mcp.tool(annotations=MUTATING, output_schema=_OUTPUT_SCHEMA, version="0.2.0")
async def gitee_corpus(
    operation: Annotated[
        Literal["search", "ingest", "status"],
        Field(
            description=(
                "Operation: 'search' runs a BM25 keyword query over indexed "
                "READMEs (which Chinese project does X?); 'ingest' fetches and "
                "indexes one repo's README; 'status' reports indexed count. "
                "READMEs are also auto-indexed when fetched via gitee_repo."
            )
        ),
    ],
    query: Annotated[
        str, Field(description="Search query (search only), e.g. 'multi-tenant low-code'.")
    ] = "",
    owner: Annotated[str, Field(description="Repo owner (ingest only).")] = "",
    repo: Annotated[str, Field(description="Repo name (ingest only).")] = "",
    limit: Annotated[int, Field(description="Max results.", ge=1, le=50)] = 10,
    ctx: Context | None = None,
) -> dict:
    """Search the local README corpus for Chinese-OSS projects.

    [RATIONALE]
    "Which Gitee project does X" is a recurring question. READMEs fetched
    through the server are indexed into a local SQLite FTS5 table and
    searched with BM25. This is honest keyword retrieval (RAG-lite) - NOT
    embeddings - for exact-fact lookups.

    ## Return Format
    {"success": bool, "operation": str, "message": str,
    "results": [...], "count": int}

    ## Examples
    gitee_corpus(operation="search", query="multi-tenant low-code")
    gitee_corpus(operation="ingest", owner="dromara", repo="hutool")
    gitee_corpus(operation="status")
    """
    if operation == "ingest":
        owner = owner.strip("/")
        repo = repo.strip("/")
        if not owner or not repo:
            return {
                "success": False,
                "operation": operation,
                "error": "owner and repo are required for ingest",
                "error_type": "validation",
                "message": "owner and repo are required for ingest",
            }
        readme = get_client().repo_readme(owner, repo)
        ok = corpus.ingest(f"{owner}/{repo}", readme)
        return {
            "success": ok,
            "operation": operation,
            "message": (
                f"Indexed {owner}/{repo} ({len(readme or '')} chars)"
                if ok and readme
                else f"{owner}/{repo} has no README to index"
                if ok
                else "index write failed"
            ),
            "count": corpus.count(),
        }
    if operation == "status":
        docs = corpus.list_indexed(limit=20)
        return {
            "success": True,
            "operation": operation,
            "count": corpus.count(),
            "indexed": docs,
            "message": f"{corpus.count()} README(s) indexed",
            "note": "BM25 keyword index (SQLite FTS5) - not embeddings.",
        }
    results = corpus.search(query, limit=limit)
    return {
        "success": True,
        "operation": operation,
        "results": results,
        "count": len(results),
        "message": f"{len(results)} README match(es) for '{query}'",
        "note": "BM25 keyword match over indexed READMEs - verify before citing.",
    }
