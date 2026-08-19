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

from . import history
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


def _fetch_seed(owner: str, repo: str, translate: bool) -> dict:
    """Fetch a seed's details + commits; raises GiteeError on failure (caller classifies)."""
    client = get_client()
    details = client.repo_details(owner, repo)
    commits = client.repo_commits(owner, repo, limit=10)
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


def _seed_error_kind(exc: GiteeError) -> str:
    """Classify a seed fetch failure: rate-limited vs dead (404) vs other."""
    if exc.error_type == "rate_limited" or exc.status in (403, 429):
        return "throttled"
    if exc.error_type == "not_found":
        return "dead"
    return "other"


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
    throttled: list[str] = []
    other_failures: list[str] = []

    # Anonymous quota exhausted? Do not burn the window with doomed requests -
    # report the honest throttled state immediately instead.
    if client.rate_limit_remaining == 0 and not client.cfg.token:
        return {
            "success": True,
            "message": (
                "Gitee anonymous rate limit exhausted (0/60 for this hour). "
                "Wait for the window to reset or set GITEE_TOKEN for the full tier."
            ),
            "data": {
                "repos": [],
                "total": 0,
                "dead_seeds": [],
                "throttled_seeds": list(seeds),
                "rate_limited": True,
                "tier": "anonymous",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        }

    for seed in seeds:
        if "/" not in seed:
            continue
        owner, repo = seed.split("/", 1)
        try:
            item = _fetch_seed(owner.strip(), repo.strip(), translate)
        except GiteeError as exc:
            kind = _seed_error_kind(exc)
            if kind == "throttled":
                throttled.append(seed)
            elif kind == "dead":
                dead.append(seed)
            else:
                other_failures.append(seed)
            logger.warning("Seed %s skipped: %s", seed, exc.message)
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

    # Attach momentum deltas (vs previous snapshot + ~7d baseline) and
    # persist this build so the next call has a baseline. First observation
    # reports momentum: null - never a fabricated 0.
    for item in results:
        mom = history.momentum_for(
            item["full_name"],
            float(item.get("activity_score") or 0),
            int(item.get("stargazers_count") or 0),
            int(item.get("forks_count") or 0),
        )
        item["momentum"] = mom["momentum"]
        item["momentum_7d"] = mom["momentum_7d"]
        item["surge"] = mom["surge"]
        item["stars_delta_7d"] = mom["stars_delta_7d"]
        item["forks_delta_7d"] = mom["forks_delta_7d"]
        item["momentum_observed_at"] = mom["observed_at"]
    history.record_snapshot(results)

    message = f"Humming radar: {len(results)} repos"
    if throttled:
        message += f", {len(throttled)} seeds throttled by the anonymous rate limit"
    if dead:
        message += f", {len(dead)} dead seeds dropped"
    return {
        "success": True,
        "message": message,
        "data": {
            "repos": results[: max(limit, 1)],
            "total": len(results),
            "dead_seeds": dead,
            "throttled_seeds": throttled,
            "rate_limited": bool(throttled),
            "tier": "token" if client.cfg.token else "anonymous",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    }
