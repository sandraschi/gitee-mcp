"""Shared test fixtures.

The JsonCache is a real on-disk cache (data/cache). Live smoke runs can
populate it, which would poison respx-mocked tests (a cache hit skips the
mocked HTTP layer and returns live data). The radar history, watchlist and
README corpus are also on-disk state. Clear them all before every test.
"""

from __future__ import annotations

import pytest

from gitee_mcp.cache import cache
from gitee_mcp.config import DATA_DIR


@pytest.fixture(autouse=True)
def _fresh_state():
    cache.clear()
    for name in ("radar_history.jsonl", "watchlist.json", "corpus.db"):
        path = DATA_DIR / name
        if path.exists():
            path.unlink()
    yield
    cache.clear()
    for name in ("radar_history.jsonl", "watchlist.json", "corpus.db"):
        path = DATA_DIR / name
        if path.exists():
            path.unlink()
