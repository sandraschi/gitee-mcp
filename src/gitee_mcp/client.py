"""Gitee v5 API client with anonymous and token tiers.

Anonymous tier (verified 2026-08-18, no token):
  repos/{owner}/{repo}          - repo details
  repos/{owner}/{repo}/readme   - base64 README
  repos/{owner}/{repo}/languages
  repos/{owner}/{repo}/commits
  repos/{owner}/{repo}/branches
  repos/{owner}/{repo}/contents
  search/users                  - user search
  users/{login}/repos           - user repos
Rate limit: 60/hour anonymous (X-RateLimit headers).

Token tier (GITEE_TOKEN) adds:
  search/repositories           - repo search + star/forks sorting
  repos/{owner}/{repo}/stargazers

Endpoints that are NOT available (probed 2026-08-18):
  explore/trending HTML + atom  - behind anti-bot JS challenge (405)
  search.gitee.com SPA API      - redirects (301)

The "humming" radar therefore derives real activity from the anonymous
surface: seed repos + their live commit streams and star/forks counts,
ranked by an activity score. No fake data.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

import httpx

from .cache import cache
from .config import Settings, settings

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {"User-Agent": "gitee-mcp/0.1.0 (fleet sandraschi)"}


class GiteeError(Exception):
    """Raised on Gitee API failures with a structured, actionable message."""

    def __init__(
        self, message: str, error_type: str = "gitee_error", status: int | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status = status


class GiteeClient:
    def __init__(self, cfg: Settings | None = None) -> None:
        self.cfg = cfg or settings
        self.rate_limit_remaining: int | None = None
        self.rate_limit_total: int | None = None
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=self.cfg.request_timeout,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------ HTTP

    def _request(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.cfg.api_base}/{path.lstrip('/')}"
        query = dict(params or {})
        if self.cfg.token and "access_token" not in query:
            query["access_token"] = self.cfg.token
        try:
            resp = self._client.get(url, params=query)
        except httpx.HTTPError as exc:
            raise GiteeError(
                f"Network error talking to Gitee: {exc}", error_type="network_error"
            ) from exc

        self._read_rate_limits(resp)
        if resp.status_code == 404:
            raise GiteeError(
                f"Gitee 404 for {path} - repo/user not found or private",
                error_type="not_found",
                status=404,
            )
        if resp.status_code == 403:
            if self.rate_limit_remaining == 0:
                raise GiteeError(
                    "Gitee anonymous rate limit exhausted (60/hour). "
                    "Set GITEE_TOKEN for the full tier, or wait for the window to reset.",
                    error_type="rate_limited",
                    status=403,
                )
            raise GiteeError(
                "Gitee 403 - this endpoint requires a token. "
                "Set GITEE_TOKEN (free at gitee.com/profile/personal_access_tokens/new).",
                error_type="auth_required",
                status=403,
            )
        if resp.status_code == 401:
            raise GiteeError(
                "Gitee 401 - token invalid or expired. Regenerate at "
                "gitee.com/profile/personal_access_tokens and update GITEE_TOKEN.",
                error_type="auth_invalid",
                status=401,
            )
        if resp.status_code == 429:
            raise GiteeError(
                "Gitee rate limit hit - slow down or set GITEE_TOKEN.",
                error_type="rate_limited",
                status=429,
            )
        if resp.status_code >= 400:
            raise GiteeError(
                f"Gitee API error {resp.status_code} for {path}: {resp.text[:300]}",
                status=resp.status_code,
            )
        return resp.json()

    def _read_rate_limits(self, resp: httpx.Response) -> None:
        try:
            self.rate_limit_total = int(
                resp.headers.get("X-RateLimit-Limit", self.rate_limit_total or 60)
            )
            self.rate_limit_remaining = int(
                resp.headers.get("X-RateLimit-Remaining", self.rate_limit_remaining)
            )
        except (TypeError, ValueError):
            pass

    # ------------------------------------------------------------ anonymous

    def repo_details(self, owner: str, repo: str, use_cache: bool = True) -> dict:
        key = f"repo:{owner}/{repo}"
        if use_cache:
            hit = cache.get(key)
            if hit is not None:
                return hit
        data = self._request(f"repos/{owner}/{repo}")
        if use_cache:
            cache.set(key, data)
        return data

    def repo_readme(self, owner: str, repo: str) -> str | None:
        key = f"readme:{owner}/{repo}"
        if (hit := cache.get(key)) is not None:
            return hit
        try:
            data = self._request(f"repos/{owner}/{repo}/readme")
        except GiteeError as exc:
            if exc.error_type == "not_found":
                cache.set(key, None)
                return None
            raise
        content = data.get("content", "")
        try:
            text = base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            text = content
        cache.set(key, text)
        return text

    def repo_languages(self, owner: str, repo: str) -> list[dict]:
        key = f"lang:{owner}/{repo}"
        if (hit := cache.get(key)) is not None:
            return hit
        data = self._request(f"repos/{owner}/{repo}/languages")
        languages = data.get("languages", [])
        cache.set(key, languages)
        return languages

    def repo_commits(self, owner: str, repo: str, limit: int = 10) -> list[dict]:
        data = self._request(f"repos/{owner}/{repo}/commits", {"per_page": min(limit, 100)})
        return data if isinstance(data, list) else []

    def repo_branches(self, owner: str, repo: str) -> list[dict]:
        key = f"branches:{owner}/{repo}"
        if (hit := cache.get(key)) is not None:
            return hit
        data = self._request(f"repos/{owner}/{repo}/branches")
        branches = data if isinstance(data, list) else []
        cache.set(key, branches)
        return branches

    def repo_contents(self, owner: str, repo: str, path: str = "") -> list[dict]:
        key = f"contents:{owner}/{repo}/{path}"
        if (hit := cache.get(key)) is not None:
            return hit
        endpoint = f"repos/{owner}/{repo}/contents"
        if path:
            endpoint += f"/{path.strip('/')}"
        data = self._request(endpoint)
        items = data if isinstance(data, list) else []
        cache.set(key, items)
        return items

    def repo_releases(self, owner: str, repo: str, limit: int = 5) -> list[dict]:
        key = f"releases:{owner}/{repo}"
        if (hit := cache.get(key)) is not None:
            return hit[:limit]
        data = self._request(f"repos/{owner}/{repo}/releases", {"per_page": min(limit, 20)})
        releases = data if isinstance(data, list) else []
        cache.set(key, releases)
        return releases[:limit]

    def search_users(self, query: str, limit: int = 10) -> list[dict]:
        data = self._request("search/users", {"q": query, "per_page": min(limit, 100)})
        return data if isinstance(data, list) else []

    def user_repos(self, login: str, limit: int = 20, sort: str = "pushed") -> list[dict]:
        data = self._request(f"users/{login}/repos", {"per_page": min(limit, 100), "sort": sort})
        return data if isinstance(data, list) else []

    def user_details(self, login: str) -> dict:
        key = f"user:{login}"
        if (hit := cache.get(key)) is not None:
            return hit
        data = self._request(f"users/{login}")
        cache.set(key, data)
        return data

    # ---------------------------------------------------------------- token

    def search_repositories(
        self,
        query: str,
        sort: str = "stargazers_count",
        order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[int, list[dict]]:
        if not self.cfg.token:
            raise GiteeError(
                "Repository search requires a Gitee token (anonymous tier returns nothing). "
                "Set GITEE_TOKEN - free at gitee.com/profile/personal_access_tokens/new.",
                error_type="auth_required",
            )
        data = self._request(
            "search/repositories",
            {
                "q": query,
                "sort": sort,
                "order": order,
                "page": page,
                "per_page": min(per_page, 100),
            },
        )
        return data.get("total_count", 0), data.get("items", [])

    def stargazers(self, owner: str, repo: str, limit: int = 10) -> list[dict]:
        if not self.cfg.token:
            raise GiteeError("Stargazer lists require GITEE_TOKEN.", error_type="auth_required")
        data = self._request(f"repos/{owner}/{repo}/stargazers", {"per_page": min(limit, 100)})
        return data if isinstance(data, list) else []

    # --------------------------------------------------------------- helpers

    def status_snapshot(self) -> dict:
        return {
            "tier": "token" if self.cfg.token else "anonymous",
            "configured": self.cfg.configured,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_total": self.rate_limit_total,
        }

    def close(self) -> None:
        self._client.close()


def activity_score(repo: dict, commits: list[dict], now_ts: float | None = None) -> float:
    """Rank "what's humming": recent commit recency + volume, plus star/forks mass."""
    now_ts = now_ts or time.time()
    stars = float(repo.get("stargazers_count") or 0)
    forks = float(repo.get("forks_count") or 0)
    score = 0.0
    recent = 0
    for commit in commits[:10]:
        date_str = ((commit.get("commit") or {}).get("committer") or {}).get("date")
        if not date_str:
            continue
        try:
            ts = time.mktime(time.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            continue
        age_hours = (now_ts - ts) / 3600
        if 0 <= age_hours <= 24:
            recent += 1
            score += 2.0 / (1 + age_hours / 24)
    score += recent * 1.5
    score += min(stars, 5000) / 5000 * 3.0
    score += min(forks, 2000) / 2000 * 1.5
    return round(score, 2)


_client: GiteeClient | None = None


def get_client() -> GiteeClient:
    global _client
    if _client is None:
        _client = GiteeClient()
    return _client
