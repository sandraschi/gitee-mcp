"""Radar snapshot history - momentum deltas, anomaly detection, star series.

Every humming_radar build appends one row per repo to
data/radar_history.jsonl (gitignored, regenerable). Deltas compare the
current activity_score / stars / forks against the previous snapshot and
the snapshot ~7 days older. This is OUR observation series - it is not
Gitee's full history (Gitee exposes no star-history API) and that is
documented honestly everywhere it is surfaced.

Momentum is null on the first observation (no baseline) rather than a
fabricated 0.
"""

from __future__ import annotations

import contextlib
import json
import time
from typing import Any

from .config import DATA_DIR

_HISTORY_DB = DATA_DIR / "radar_history.jsonl"
_MAX_ROWS = 2000  # hard cap on the file (prune oldest rows)
_WINDOW_SECONDS = 7 * 86400  # 7-day momentum window
_SURGE_THRESHOLD = 3.0  # activity_score delta that counts as a surge


def _load_rows() -> list[dict[str, Any]]:
    if not _HISTORY_DB.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with _HISTORY_DB.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows


def _row_ts(row: dict[str, Any]) -> float | None:
    try:
        return float(row.get("ts") or 0)
    except (TypeError, ValueError):
        return None


def _as_float(row: dict[str, Any] | None, key: str) -> float | None:
    if row is None:
        return None
    try:
        value = row.get(key)
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_int(row: dict[str, Any] | None, key: str) -> int | None:
    if row is None:
        return None
    try:
        value = row.get(key)
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _last_for(
    full_name: str, rows: list[dict[str, Any]], before_ts: float
) -> dict[str, Any] | None:
    """Most recent row for a repo with ts < before_ts (strictly before the current build)."""
    candidate: dict[str, Any] | None = None
    for row in rows:
        if row.get("repo") != full_name:
            continue
        row_ts = _row_ts(row)
        if row_ts is None or not (0 < row_ts < before_ts):
            continue
        candidate_ts = _row_ts(candidate) if candidate is not None else None
        if candidate is None or candidate_ts is None or row_ts > candidate_ts:
            candidate = row
    return candidate


def _about_days_ago(
    full_name: str, rows: list[dict[str, Any]], before_ts: float, days: int
) -> dict[str, Any] | None:
    """Row for a repo closest to (before_ts - days*86400), strictly in the past."""
    target = before_ts - days * 86400
    best: dict[str, Any] | None = None
    best_gap: float | None = None
    for row in rows:
        if row.get("repo") != full_name:
            continue
        row_ts = _row_ts(row)
        if row_ts is None or not (0 < row_ts < before_ts):
            continue
        gap = abs(row_ts - target)
        if best_gap is None or gap < best_gap:
            best = row
            best_gap = gap
    return best


def momentum_for(
    full_name: str,
    activity_score: float,
    stargazers: int,
    forks: int,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Deltas vs previous snapshot and the ~7-day-old snapshot.

    Returns {"momentum": float|None, "momentum_7d": float|None,
    "stars_delta_7d": int, "forks_delta_7d": int, "surge": bool,
    "observed_at": str}.
    """
    now_ts = now_ts or time.time()
    rows = _load_rows()
    prev = _last_for(full_name, rows, now_ts)
    week = _about_days_ago(full_name, rows, now_ts, 7)

    prev_score = _as_float(prev, "activity_score")
    week_score = _as_float(week, "activity_score")
    week_stars = _as_int(week, "stargazers_count")
    week_forks = _as_int(week, "forks_count")

    momentum = round(activity_score - prev_score, 2) if prev_score is not None else None
    momentum_7d = round(activity_score - week_score, 2) if week_score is not None else None

    return {
        "momentum": momentum,
        "momentum_7d": momentum_7d,
        "stars_delta_7d": (stargazers - week_stars) if week_stars is not None else None,
        "forks_delta_7d": (forks - week_forks) if week_forks is not None else None,
        "surge": bool(momentum is not None and momentum >= _SURGE_THRESHOLD),
        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts)),
    }


def record_snapshot(repos: list[dict], now_ts: float | None = None) -> None:
    """Append one row per repo (activity_score, stars, forks). Best-effort."""
    now_ts = now_ts or time.time()
    try:
        _HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    lines = []
    for repo in repos:
        if not repo.get("full_name"):
            continue
        row = {
            "ts": now_ts,
            "repo": repo.get("full_name", ""),
            "activity_score": repo.get("activity_score"),
            "stargazers_count": repo.get("stargazers_count") or 0,
            "forks_count": repo.get("forks_count") or 0,
        }
        lines.append(json.dumps(row, ensure_ascii=False))
    if not lines:
        return
    try:
        with _HISTORY_DB.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError:
        return
    _prune()


def _prune() -> None:
    rows = _load_rows()
    if len(rows) <= _MAX_ROWS:
        return
    rows = rows[-_MAX_ROWS:]
    with contextlib.suppress(OSError):
        _HISTORY_DB.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )


def star_history(full_name: str, limit: int = 30) -> list[dict]:
    """Observed stars/forks/activity series for a repo, oldest first."""
    rows = [r for r in _load_rows() if r.get("repo") == full_name]
    rows.sort(key=lambda r: _row_ts(r) or 0)
    return [
        {
            "ts": r.get("ts"),
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_row_ts(r) or 0)),
            "activity_score": r.get("activity_score"),
            "stargazers_count": r.get("stargazers_count"),
            "forks_count": r.get("forks_count"),
        }
        for r in rows[-max(limit, 1) :]
    ]


def top_movers(days: int = 7, limit: int = 10) -> list[dict]:
    """Rank repos by activity delta over the window, oldest-first baselines.

    Returns [{full_name, delta, current_score, prev_score, stars_delta,
    forks_delta}] sorted by descending delta. Only repos with a baseline
    within the window and a current observation are included.
    """
    rows = _load_rows()
    now_ts = time.time()
    window_start = now_ts - days * 86400
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        row_ts = _row_ts(row)
        if row_ts is None or row_ts < window_start:
            continue
        by_repo.setdefault(str(row.get("repo", "")), []).append(row)

    movers: list[dict] = []
    for full_name, series in by_repo.items():
        if not full_name:
            continue
        series.sort(key=lambda r: _row_ts(r) or 0)
        first = series[0]
        last = series[-1]
        first_score = _as_float(first, "activity_score")
        last_score = _as_float(last, "activity_score")
        if first_score is None or last_score is None:
            continue
        if first is last:
            continue  # only one observation in the window - no delta
        movers.append(
            {
                "full_name": full_name,
                "delta": round(last_score - first_score, 2),
                "current_score": round(last_score, 2),
                "prev_score": round(first_score, 2),
                "stars_delta": (_as_int(last, "stargazers_count") or 0)
                - (_as_int(first, "stargazers_count") or 0),
                "forks_delta": (_as_int(last, "forks_count") or 0)
                - (_as_int(first, "forks_count") or 0),
            }
        )
    movers.sort(key=lambda m: m["delta"], reverse=True)
    return movers[: max(limit, 1)]
