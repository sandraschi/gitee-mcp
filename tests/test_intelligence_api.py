"""REST endpoint tests for the v0.2 ecosystem-intelligence surface."""

from __future__ import annotations

import time

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

import gitee_mcp.client as client_mod
import gitee_mcp.server as server

FAKE_REPO = {
    "full_name": "dromara/hutool",
    "name": "hutool",
    "owner": {"login": "dromara"},
    "html_url": "https://gitee.com/dromara/hutool.git",
    "description": "企业级Java工具类库",
    "language": "Java",
    "stargazers_count": 23000,
    "forks_count": 9000,
    "watchers_count": 5000,
    "open_issues_count": 40,
    "default_branch": "master",
    "created_at": "2020-01-01T00:00:00+08:00",
    "pushed_at": "2026-08-17T10:00:00+08:00",
    "license": {"name": "Apache-2.0"},
    "homepage": None,
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(server.app)


@respx.mock
def test_watchlist_roundtrip(client: TestClient):
    r = client.post("/api/watchlist", json={"full_name": "dromara/hutool"})
    assert r.status_code == 200
    r = client.get("/api/watchlist")
    assert any(e["full_name"] == "dromara/hutool" for e in r.json()["entries"])
    r = client.delete("/api/watchlist/dromara/hutool")
    assert r.json()["removed"] is True


def test_corpus_endpoints(client: TestClient):
    import gitee_mcp.corpus as corpus

    corpus.ingest("a/b", "multi-tenant 权限管理")
    r = client.get("/api/corpus/search", params={"q": "权限管理"})
    assert r.status_code == 200
    assert any(h["full_name"] == "a/b" for h in r.json()["results"])
    r = client.get("/api/corpus/status")
    assert r.json()["count"] >= 1


def test_explore_momentum_no_history_is_honest(client: TestClient):
    r = client.get("/api/explore/momentum")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "radar history" in body["note"]


@respx.mock
def test_ecosystem_graph_endpoint(client: TestClient):
    from gitee_mcp.config import settings

    old_client = client_mod._client
    old_seeds = settings.seed_repos
    settings.seed_repos = ["dromara/hutool"]
    client_mod._client = type(
        "C",
        (),
        {
            "cfg": settings,
            "rate_limit_remaining": None,
            "repo_details": lambda self, o, r: {
                **FAKE_REPO,
                "full_name": f"{o}/{r}",
                "parent": None,
                "fork": False,
            },
        },
    )()
    try:
        r = client.get("/api/ecosystem/graph", params={"scope": "seeds"})
        assert r.status_code == 200
        assert r.json()["counts"]["nodes"] >= 2
    finally:
        client_mod._client = old_client
        settings.seed_repos = old_seeds


@respx.mock
def test_mirror_endpoint_not_found(client: TestClient):
    respx.get("https://api.github.com/repos/gitee/only").mock(return_value=Response(404, json={}))
    r = client.get("/api/ecosystem/mirror/gitee/only")
    assert r.status_code == 200
    assert r.json()["on_github"] is False


def test_feed_xml_endpoint(client: TestClient):
    r = client.get("/api/feed.xml")
    assert r.status_code == 200
    assert "<rss" in r.json()["feed_xml"] or r.json()["success"] is True


def test_translate_explain_endpoint(client: TestClient):
    from gitee_mcp.translate import translator

    translator._healthy = False
    translator._last_check = time.time()
    r = client.post("/api/translate/explain", json={"text": "RuoYi"})
    assert r.status_code == 200
    assert r.json()["source"] == "fact-sheet"


def test_webhook_digest_endpoint(client: TestClient):
    client.post(
        "/api/webhooks/gitee",
        json={"repository": {"full_name": "x/y"}},
        headers={"X-Gitee-Event": "Push Hook"},
    )
    r = client.get("/api/webhooks/digest")
    assert r.status_code == 200
    assert r.json()["event_count"] >= 1


def test_new_tools_registered():
    import asyncio

    import gitee_mcp.tools  # noqa: F401
    from gitee_mcp.server_state import mcp

    names = sorted(t.name for t in asyncio.run(mcp.list_tools()))
    for expected in (
        "gitee_watchlist",
        "gitee_ecosystem",
        "gitee_corpus",
        "gitee_shutdown",
    ):
        assert expected in names, f"missing tool {expected}"
