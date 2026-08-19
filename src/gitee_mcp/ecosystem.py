"""Ecosystem intelligence (F9/F10/F14).

- graph: orgs + their seed/watchlist repos + fork relationships. Nodes and
  edges are real (repo details carry `parent`/`fork` when Gitee reports
  them); the graph is honest about what it does NOT have (contributor
  overlap needs the events API - documented, not fabricated).
- mirror: compares a repo against its GitHub twin via the public GitHub
  API (cached 1h). Returns "not found" for Gitee-only projects.
- digest: weekly "who's rising" narrative built from radar history deltas.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from . import history
from .cache import cache
from .client import GiteeError, get_client
from .config import DATA_DIR, settings
from .translate import translator
from .watchlist import list_entries

logger = logging.getLogger(__name__)

_MIRROR_TTL = 3600  # GitHub public API is 60 req/hr unauthenticated


def _parent_full_name(details: dict) -> str | None:
    parent = details.get("parent")
    if isinstance(parent, dict):
        return parent.get("full_name")
    return None


def build_graph(scope: str = "seeds") -> dict[str, Any]:
    """Org/repo graph from seed or watchlist repos.

    nodes: {id, kind: org|repo, label}
    edges: {source, target, relation: owns|forked_from}
    """
    if scope not in ("seeds", "watchlist"):
        scope = "seeds"
    if scope == "seeds":
        repos = [r for r in settings.seed_repos if "/" in r]
    else:
        repos = [e.full_name for e in list_entries() if "/" in e.full_name]

    client = get_client()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def _ensure_org(org: str) -> None:
        if org and org not in nodes:
            nodes[org] = {"id": org, "kind": "org", "label": org}

    for full in repos:
        owner, _, repo = full.partition("/")
        _ensure_org(owner)
        repo_id = full
        if repo_id not in nodes:
            nodes[repo_id] = {"id": repo_id, "kind": "repo", "label": repo_id}
        edges.append({"source": owner, "target": repo_id, "relation": "owns"})
        try:
            details = client.repo_details(owner, repo)
        except GiteeError:
            continue
        parent = _parent_full_name(details)
        if parent and parent != full and parent not in nodes:
            nodes[parent] = {"id": parent, "kind": "repo", "label": parent}
        if parent and parent != full:
            edges.append({"source": repo_id, "target": parent, "relation": "forked_from"})

    return {
        "success": True,
        "scope": scope,
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": edges,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
        "note": "Contributor-overlap edges require the Gitee events API (rate-heavy) - not included.",
    }


def mirror_compare(owner: str, repo: str) -> dict[str, Any]:
    """Compare a repo with its GitHub twin (public API, cached 1h)."""
    owner = owner.strip("/")
    repo = repo.strip("/")
    key = f"github-mirror:{owner}/{repo}"
    if (hit := cache.get(key)) is not None:
        hit["cached"] = True
        return hit

    url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        resp = httpx.get(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "gitee-mcp"},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        return {
            "success": False,
            "error": f"GitHub API unreachable: {exc}",
            "error_type": "network_error",
            "cached": False,
        }
    if resp.status_code == 404:
        result = {
            "success": True,
            "on_github": False,
            "owner": owner,
            "repo": repo,
            "note": f"{owner}/{repo} was not found on GitHub - this project may be Gitee-only.",
            "cached": False,
        }
        cache.set(key, result)
        return result
    if resp.status_code == 403:
        return {
            "success": False,
            "error": "GitHub API rate limit hit (60/hr unauthenticated).",
            "error_type": "rate_limited",
            "cached": False,
        }
    if resp.status_code >= 400:
        return {
            "success": False,
            "error": f"GitHub API error {resp.status_code}",
            "error_type": "github_error",
            "cached": False,
        }

    g = resp.json()
    try:
        gh_stars = int(g.get("stargazers_count") or 0)
        gh_forks = int(g.get("forks_count") or 0)
    except (TypeError, ValueError):
        gh_stars = gh_forks = 0

    # Gitee side (cached 10 min) for the delta
    gitee_stars = gitee_forks = None
    gitee_pushed = None
    try:
        details = get_client().repo_details(owner, repo)
        gitee_stars = int(details.get("stargazers_count") or 0)
        gitee_forks = int(details.get("forks_count") or 0)
        gitee_pushed = details.get("pushed_at")
    except (GiteeError, TypeError, ValueError):
        pass

    result = {
        "success": True,
        "on_github": True,
        "owner": owner,
        "repo": repo,
        "github": {
            "stargazers_count": gh_stars,
            "forks_count": gh_forks,
            "pushed_at": g.get("pushed_at"),
            "description": g.get("description"),
            "language": g.get("language"),
            "html_url": g.get("html_url"),
        },
        "gitee": {
            "stargazers_count": gitee_stars,
            "forks_count": gitee_forks,
            "pushed_at": gitee_pushed,
        },
        "delta": (
            {
                "stars": (gitee_stars - gh_stars) if gitee_stars is not None else None,
                "forks": (gitee_forks - gh_forks) if gitee_forks is not None else None,
            }
            if gitee_stars is not None
            else None
        ),
        "cached": False,
    }
    cache.set(key, result)
    return result


def _narrative(movers: list[dict], days: int) -> str:
    lines = [f"# gitee-mcp weekly digest - last {days} days", ""]
    if not movers:
        lines.append(
            "Not enough history yet. Run the radar a few times over "
            "separate days to build momentum baselines."
        )
        return "\n".join(lines)
    lines.append("## Top movers (activity score delta)")
    for m in movers:
        lines.append(
            f"- **{m['full_name']}**: +{m['delta']:.2f} "
            f"({m['current_score']:.2f} vs {m['prev_score']:.2f}, "
            f"stars {m['stars_delta']:+d}, forks {m['forks_delta']:+d})"
        )
    surged = [m for m in movers if m["delta"] >= 3.0]
    if surged:
        lines.append("")
        lines.append("## Surges (>= +3.0 activity)")
        for m in surged:
            lines.append(f"- {m['full_name']} (+{m['delta']:.2f})")
    dropped = [m for m in movers if m["delta"] <= -2.0]
    if dropped:
        lines.append("")
        lines.append("## Slowing down (<= -2.0 activity)")
        for m in dropped:
            lines.append(f"- {m['full_name']} ({m['delta']:.2f})")
    lines.append("")
    lines.append("Data: gitee-mcp radar history (our observations, not Gitee's full history).")
    return "\n".join(lines)


def weekly_digest(days: int = 7, limit: int = 12, write_file: bool = True) -> dict[str, Any]:
    """Generate the weekly 'who's rising' narrative from history deltas."""
    movers = history.top_movers(days=days, limit=limit)
    narrative = _narrative(movers, days)

    # LLM polish pass when a provider is up (fallback stays the template).
    polished = False
    health = translator.provider_health()
    if health["available"] and movers:
        try:
            movers_text = "\n".join(
                f"- {m['full_name']}: delta {m['delta']:+.2f}, stars {m['stars_delta']:+d}"
                for m in movers
            )
            resp = httpx.post(
                f"{settings.llm_base_url}/chat/completions",
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You write a short weekly Chinese-OSS ecosystem brief from data. Plain text.",
                        },
                        {
                            "role": "user",
                            "content": f"Write a 5-8 sentence brief. Highlight the biggest movers, any patterns (e.g. a tech family rising), and what slowed down.\n\n{movers_text}",
                        },
                    ],
                    "temperature": 0.4,
                    "max_tokens": 500,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            brief = (resp.json()["choices"][0]["message"]["content"] or "").strip()
            if brief:
                narrative = narrative.replace(
                    "## Top movers", f"## Brief\n\n{brief}\n\n## Top movers", 1
                )
                polished = True
        except (httpx.HTTPError, ValueError, KeyError):
            pass

    if write_file:
        try:
            path = DATA_DIR / "digest-latest.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(narrative, encoding="utf-8")
        except OSError:
            pass

    return {
        "success": True,
        "days": days,
        "narrative": narrative,
        "movers": movers,
        "polished": polished,
        "source": "radar-history",
    }
