"""Shared test fixtures.

The JsonCache is a real on-disk cache (data/cache). Live smoke runs can
populate it, which would poison respx-mocked tests (a cache hit skips the
mocked HTTP layer and returns live data). Clear it before every test.
"""

from __future__ import annotations

import pytest

from gitee_mcp.cache import cache


@pytest.fixture(autouse=True)
def _fresh_cache():
    cache.clear()
    yield
    cache.clear()
