"""The "what's humming on Gitee" radar.

Anonymous tier cannot query a trending endpoint (explore pages are behind an
anti-bot challenge, repo search needs a token - both verified 2026-08-18).
So the radar derives real activity from the anonymous surface:

  1. Seed repos (curated popular Gitee projects, or GITEE_SEED_REPOS)
  2. Live details + recent commits for each seed (real API calls, cached)
  3. activity_score() ranks by commit recency/volume + star/forks mass

Seeds that 404 are dropped and reported - no silent dead weight.
With GITEE_TOKEN the radar also mixes in search/repositories sorted by
stars so fresh popular repos enter the feed.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .client import GiteeError, activity_score, get_client
from .config import settings
from .translate import is_chinese, translator

logger = logging.getLogger(__name__)

TRACKED_LANGUAGES = {
    "python",
    "java",
    "go",
    "rust",
    "javascript",
    "typescript",
    "c",
    "c++",
    "vue",
    "kotlin",
    "swift",
    "php",
    "dart",
    "ruby",
    "lua",
    "c#",
}


def _enrich(repo: dict, translate: bool) -> dict:
    description = repo.get("description") or ""
    out = {
        "full_name": repo.get("full_name") or "",
        "name": repo.get("name") or "",
        "owner": ((repo.get("owner") or {}).get("login") or "")
        or ((repo.get("namespace") or {}).get("path") or ""),
        "html_url": (repo.get("html_url") or "").replace(".git", ""),
        "description": description,
        "language": repo.get("language"),
        "stargazers_count": repo.get("stargazers_count") or 0,
        "forks_count": repo.get("forks_count") or 0,
        "watchers_count": repo.get("watchers_count") or 0,
        "open_issues_count": repo.get("open_issues_count") or 0,
        "default_branch": repo.get("default_branch") or "master",
        "created_at": repo.get("created_at"),
        "pushed_at": repo.get("pushed_at"),
        "license": (repo.get("license") or {}).get("name")
        if isinstance(repo.get("license"), dict)
        else None,
        "homepage": repo.get("homepage"),
        "need_translation": is_chinese(description),
        "translation": "",
    }
    if translate and out["need_translation"] and out["description"]:
        result = translator.zh_to_en(out["description"])
        out["translation"] = result.get("translation", "")
        out["translation_note"] = result.get("note", "") if not result.get("translated") else ""
    return out


def _fetch_seed(owner: str, repo: str, translate: bool) -> dict | None:
    client = get_client()
    try:
        details = client.repo_details(owner, repo)
        commits = client.repo_commits(owner, repo, limit=10)
    except GiteeError as exc:
        logger.warning("Seed %s/%s failed: %s", owner, repo, exc.message)
        return None
    enriched = _enrich(details, translate)
    enriched["activity_score"] = activity_score(details, commits)
    enriched["recent_commits"] = [
        {
            "sha": c.get("sha", "")[:8],
            "message": ((c.get("commit") or {}).get("message") or "").splitlines()[0][:120],
            "date": ((c.get("commit") or {}).get("committer") or {}).get("date"),
            "author": (((c.get("commit") or {}).get("author") or {}).get("name")) or "",
        }
        for c in commits[:5]
    ]
    return enriched


def humming_radar(
    limit: int = 20,
    language: str = "",
    translate: bool = False,
    token_mix: bool = True,
) -> dict[str, Any]:
    """Ranked live snapshot of what is humming on Gitee right now."""
    client = get_client()
    seeds = settings.seed_repos
    results: list[dict] = []
    dead: list[str] = []

    for seed in seeds:
        if "/" not in seed:
            continue
        owner, repo = seed.split("/", 1)
        item = _fetch_seed(owner.strip(), repo.strip(), translate)
        if item is None:
            dead.append(seed)
            continue
        if language and (item["language"] or "").lower() != language.lower():
            continue
        results.append(item)

    # Token tier: mix in top-starred search results so fresh hits enter the feed
    if token_mix and client.cfg.token:
        try:
            _, top = client.search_repositories("stars:>100", sort="stargazers_count", per_page=10)
            known = {r["full_name"] for r in results}
            for repo in top:
                full = repo.get("full_name") or ""
                if full and full not in known:
                    item = _enrich(repo, translate)
                    item["activity_score"] = activity_score(repo, [])
                    results.append(item)
        except GiteeError as exc:
            logger.warning("Token mix skipped: %s", exc.message)

    results.sort(key=lambda r: r.get("activity_score", 0), reverse=True)
    return {
        "success": True,
        "message": f"Humming radar: {len(results)} repos, {len(dead)} dead seeds dropped",
        "data": {
            "repos": results[: max(limit, 1)],
            "total": len(results),
            "dead_seeds": dead,
            "tier": "token" if client.cfg.token else "anonymous",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    }
