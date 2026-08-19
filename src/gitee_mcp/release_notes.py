"""Release-notes summarizer (F6).

Fetches a repo's releases from the Gitee v5 API (cached) and translates /
summarizes the latest body to English via the local LLM, with a glossary
fallback when the provider is down. Never fakes a summary - the raw body
is always returned alongside for verification.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .client import get_client
from .config import settings
from .translate import gloss, is_chinese, translator

logger = logging.getLogger(__name__)


def latest_releases(owner: str, repo: str, limit: int = 3) -> list[dict]:
    """Slim release list: tag, name, date, body (truncated), is_prerelease."""
    data = get_client().repo_releases(owner, repo, limit=max(limit, 1))
    out = []
    for rel in data:
        body = rel.get("body") or ""
        out.append(
            {
                "tag_name": rel.get("tag_name"),
                "name": rel.get("name") or rel.get("tag_name"),
                "published_at": rel.get("published_at") or rel.get("created_at"),
                "prerelease": bool(rel.get("prerelease")),
                "html_url": rel.get("html_url"),
                "body": body[:4000],
                "is_chinese": is_chinese(body),
            }
        )
    return out[: max(limit, 1)]


def summarize_latest(owner: str, repo: str, limit: int = 3) -> dict[str, Any]:
    """Summarize the newest release body in English; fallback = glossary gloss."""
    releases = latest_releases(owner, repo, limit)
    if not releases:
        return {
            "success": True,
            "has_releases": False,
            "message": f"{owner}/{repo} has no releases on Gitee",
            "releases": [],
        }
    latest = releases[0]
    body = latest["body"] or ""
    health = translator.provider_health()
    if not body:
        return {
            "success": True,
            "has_releases": True,
            "summary": "(no release body published)",
            "releases": releases,
            "translated": False,
        }
    if not health["available"]:
        return {
            "success": True,
            "has_releases": True,
            "summary": gloss(body) if is_chinese(body) else body[:2000],
            "releases": releases,
            "translated": False,
            "note": "Local LLM unreachable; gloss/raw body only.",
        }
    prompt = (
        "Summarize the following Chinese software release notes into 3-6 "
        "concise English bullet points. Preserve version numbers, dates and "
        "key feature names. Reply with bullet points only.\n\n"
        f"Repo: {owner}/{repo}  Tag: {latest.get('tag_name')}\n\n{body[:3000]}"
    )
    try:
        resp = httpx.post(
            f"{settings.llm_base_url}/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You summarize release notes to concise English bullets.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 600,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        content = (resp.json()["choices"][0]["message"]["content"] or "").strip()
        if not content:
            raise ValueError("empty completion")
        return {
            "success": True,
            "has_releases": True,
            "summary": content,
            "releases": releases,
            "translated": True,
            "model": settings.llm_model,
        }
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Release summary failed (%s) - raw body fallback", exc.__class__.__name__)
        return {
            "success": True,
            "has_releases": True,
            "summary": gloss(body) if is_chinese(body) else body[:2000],
            "releases": releases,
            "translated": False,
            "note": f"LLM summarize failed ({exc.__class__.__name__}); raw/gloss body.",
        }
