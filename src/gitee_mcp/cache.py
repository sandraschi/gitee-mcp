"""Tiny JSON file cache for Gitee API responses.

Purpose: the anonymous Gitee tier is rate-limited to ~60 requests/hour.
Without caching, one webapp page load burns the quota. Cache lives under
data/cache (gitignored) and is keyed per endpoint+params with a TTL.
"""

from __future__ import annotations

import contextlib
import json
import time
from pathlib import Path

from .config import DATA_DIR

_CACHE_DIR = DATA_DIR / "cache"


class JsonCache:
    def __init__(self, ttl: int = 600, namespace: str = "gitee") -> None:
        self.ttl = ttl
        self._dir = _CACHE_DIR / namespace
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)[:120]
        return self._dir / f"{safe}.json"

    def get(self, key: str):
        path = self._path(key)
        if not path.exists():
            return None
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - blob.get("_ts", 0) > self.ttl:
            return None
        return blob.get("data")

    def set(self, key: str, data) -> None:
        path = self._path(key)
        # cache is best-effort; never crash the server
        with contextlib.suppress(OSError):
            path.write_text(
                json.dumps({"_ts": time.time(), "data": data}, ensure_ascii=False),
                encoding="utf-8",
            )

    def clear(self) -> int:
        removed = 0
        for path in self._dir.glob("*.json"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
        return removed


cache = JsonCache()
