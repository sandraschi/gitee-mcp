"""Embeddable radar feed (F7) - RSS 2.0 from the humming radar.

Lets anyone subscribe to "Chinese OSS now" in a feed reader. Items are the
current radar repos with their activity scores; the feed is regenerated on
each request (cheap - it reuses the cached radar). No fabricated items:
the feed is empty with a note when the radar is rate-limited.
"""

from __future__ import annotations

import html
import time

from .radar import humming_radar

_TITLE = "gitee-mcp - What is humming on Gitee"
_LINK = "http://127.0.0.1:11161/api/feed.xml"
_DESC = "Live, computed activity ranking of the Chinese open-source ecosystem (gitee-mcp radar)."


def _esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def build_feed(limit: int = 20, translate: bool = False) -> str:
    result = humming_radar(limit=limit, translate=translate)
    repos = result.get("data", {}).get("repos", [])
    now_rfc = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    items = []
    for repo in repos[: max(limit, 1)]:
        name = repo.get("full_name", "")
        desc = repo.get("description") or "(no description)"
        if repo.get("translation"):
            desc = f"{desc} | {repo['translation']}"
        lang = repo.get("language") or "-"
        stars = repo.get("stargazers_count", 0)
        activity = repo.get("activity_score", 0)
        items.append(
            "<item>\n"
            f"<title>{_esc(f'{name} ({lang}, {stars} stars, activity {activity})')}</title>\n"
            f"<link>{_esc(f'https://gitee.com/{name}')}</link>\n"
            f'<guid isPermaLink="false">{_esc(f"{name}-{activity}")}</guid>\n'
            f"<description>{_esc(desc)}</description>\n"
            "</item>"
        )
    message = result.get("message", "")
    rate_limited = bool(result.get("data", {}).get("rate_limited"))
    if rate_limited:
        message += " (rate-limited - empty until the window resets)"
    body = "\n".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "<channel>\n"
        f"<title>{_esc(_TITLE)}</title>\n"
        f"<link>{_esc(_LINK)}</link>\n"
        f"<description>{_esc(_DESC)}</description>\n"
        f"<lastBuildDate>{now_rfc}</lastBuildDate>\n"
        f"<generator>gitee-mcp {time.strftime('%Y-%m-%d', time.gmtime())}</generator>\n"
        f"<docs>{_esc(_LINK)}</docs>\n"
        f"<comment>{_esc(message)}</comment>\n"
        f"{body}\n"
        "</channel>\n"
        "</rss>\n"
    )
