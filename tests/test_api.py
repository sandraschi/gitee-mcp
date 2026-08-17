"""REST API surface tests - declared respx doubles, no live network."""

from __future__ import annotations

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

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


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["tool_count"] >= 8


def test_capabilities(client: TestClient):
    r = client.get("/api/capabilities")
    assert r.status_code == 200
    assert r.json()["features"]["translate"] is True


def test_tools_list(client: TestClient):
    r = client.get("/api/tools")
    assert r.status_code == 200
    names = r.json()["tools"]
    assert "gitee_explore" in names
    assert "gitee_repo" in names


def test_skills(client: TestClient):
    r = client.get("/api/skills")
    assert r.status_code == 200
    assert r.json()["skills"][0]["name"] == "gitee-expert"
    content = client.get("/api/skills/gitee-expert")
    assert "gitee_explore" in content.text


def test_dashboard(client: TestClient):
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert "tier" in body
    assert "seed_count" in body


def test_llm_discover(client: TestClient):
    r = client.get("/api/llm/discover")
    assert r.status_code == 200
    assert "providers" in r.json()


def test_llm_chat_unreachable_returns_error(client: TestClient):
    r = client.post("/api/llm/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "error_type" in body


def test_translate_empty_validation(client: TestClient):
    r = client.post("/api/translate", json={"text": ""})
    assert r.status_code == 200
    assert r.json()["translated"] is False


def test_webhook_secret_rejected(client: TestClient):
    import gitee_mcp.config as config

    old = config.settings.webhook_secret
    config.settings.webhook_secret = "sekrit"
    try:
        r = client.post("/api/webhooks/gitee", json={}, headers={"X-Gitee-Token": "wrong"})
        assert r.status_code == 403
    finally:
        config.settings.webhook_secret = old


def test_webhook_accepts_and_lists(client: TestClient):
    r = client.post(
        "/api/webhooks/gitee",
        json={"repository": {"full_name": "x/y"}},
        headers={"X-Gitee-Event": "Push Hook"},
    )
    assert r.status_code == 200
    assert r.json()["success"] is True
    events = client.get("/api/webhooks/events")
    assert events.json()["count"] >= 1


@respx.mock
def test_repo_surface_proxies_tool(client: TestClient):
    respx.get("https://gitee.com/api/v5/repos/dromara/hutool").mock(
        return_value=Response(200, json=FAKE_REPO)
    )
    r = client.get("/api/repos/dromara/hutool/details")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"]["full_name"] == "dromara/hutool"


def test_logs_ring(client: TestClient):
    r = client.get("/api/logs")
    assert r.status_code == 200
    assert isinstance(r.json()["logs"], list)
