"""Persistent repo watchlist with change detection (F5).

A user-curated list of repos persisted to data/watchlist.json. `check`
re-fetches each repo's recent commits and reports what changed since the
last check (by sha) plus optional activity/threshold crossing
(auto-follow signal). Local-only, regenerable, never invented.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field

from .client import GiteeClient, GiteeError, get_client
from .config import DATA_DIR

_WATCHLIST_DB = DATA_DIR / "watchlist.json"


@dataclass
class WatchEntry:
    full_name: str
    added_at: float = field(default_factory=time.time)
    min_activity: float | None = None
    last_check: float | None = None
    last_commit_shas: list[str] = field(default_factory=list)


def _load() -> list[WatchEntry]:
    if not _WATCHLIST_DB.exists():
        return []
    try:
        raw = json.loads(_WATCHLIST_DB.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    entries = []
    for item in raw if isinstance(raw, list) else []:
        try:
            entries.append(
                WatchEntry(
                    full_name=str(item.get("full_name", "")),
                    added_at=float(item.get("added_at") or time.time()),
                    min_activity=(
                        float(item["min_activity"])
                        if item.get("min_activity") is not None
                        else None
                    ),
                    last_check=(
                        float(item["last_check"]) if item.get("last_check") is not None else None
                    ),
                    last_commit_shas=list(item.get("last_commit_shas") or []),
                )
            )
        except (TypeError, ValueError):
            continue
    return entries


def _save(entries: list[WatchEntry]) -> None:
    try:
        _WATCHLIST_DB.parent.mkdir(parents=True, exist_ok=True)
        _WATCHLIST_DB.write_text(
            json.dumps([asdict(e) for e in entries], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def add(full_name: str, min_activity: float | None = None) -> WatchEntry:
    entries = _load()
    if any(e.full_name == full_name for e in entries):
        return next(e for e in entries if e.full_name == full_name)
    entry = WatchEntry(full_name=full_name, min_activity=min_activity)
    entries.append(entry)
    _save(entries)
    return entry


def remove(full_name: str) -> bool:
    entries = _load()
    kept = [e for e in entries if e.full_name != full_name]
    if len(kept) == len(entries):
        return False
    _save(kept)
    return True


def list_entries() -> list[WatchEntry]:
    return _load()


def _commit_shas(client: GiteeClient, full_name: str) -> tuple[list[str], float] | None:
    owner, _, repo = full_name.partition("/")
    if not owner or not repo:
        return None
    try:
        commits = client.repo_commits(owner.strip(), repo.strip(), limit=5)
    except GiteeError:
        return None
    shas = [c.get("sha", "") for c in commits if c.get("sha")]
    return shas, time.time()


def check(client: GiteeClient | None = None) -> dict:
    """Diff each watched repo against its last check. Returns per-repo report."""
    client = client or get_client()
    entries = _load()
    now = time.time()
    results = []
    changed_any = False
    for entry in entries:
        fetched = _commit_shas(client, entry.full_name)
        if fetched is None:
            results.append(
                {
                    "full_name": entry.full_name,
                    "status": "error",
                    "note": "could not fetch commits (repo gone, private, or rate-limited)",
                }
            )
            continue
        shas, ts = fetched
        new_commits = [s for s in shas if s not in set(entry.last_commit_shas)]
        entry.last_commit_shas = shas
        entry.last_check = ts
        changed = bool(new_commits) and bool(entry.last_commit_shas)
        if changed:
            changed_any = True
        results.append(
            {
                "full_name": entry.full_name,
                "status": "changed" if changed else "unchanged",
                "new_commits": len(new_commits),
                "new_commit_shas": new_commits[:5],
                "min_activity": entry.min_activity,
            }
        )
    _save(entries)
    return {
        "success": True,
        "changed_any": changed_any,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "entries": results,
        "count": len(results),
    }
