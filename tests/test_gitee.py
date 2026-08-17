"""Unit tests for gitee-mcp - declared test doubles only (respx HTTP mocking)."""

from __future__ import annotations

import base64
import time

import pytest
import respx
from httpx import Response

from gitee_mcp.client import GiteeClient, GiteeError, activity_score
from gitee_mcp.radar import _enrich, humming_radar
from gitee_mcp.translate import Translator, is_chinese

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

FAKE_COMMITS = [
    {
        "sha": "abc123",
        "commit": {
            "message": "feat: add new module",
            "author": {"name": "Dev", "date": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())},
            "committer": {"name": "Dev", "date": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())},
        },
    }
]


@pytest.fixture
def client() -> GiteeClient:
    from gitee_mcp.config import Settings

    cfg = Settings()
    cfg.token = ""
    cfg.api_base = "https://gitee.test/api/v5"
    return GiteeClient(cfg)


# ------------------------------------------------------------------ client


@respx.mock
def test_repo_details_anonymous(client: GiteeClient):
    respx.get("https://gitee.test/api/v5/repos/dromara/hutool").mock(
        return_value=Response(200, json=FAKE_REPO)
    )
    data = client.repo_details("dromara", "hutool")
    assert data["full_name"] == "dromara/hutool"


@respx.mock
def test_repo_details_404_raises_structured_error(client: GiteeClient):
    respx.get("https://gitee.test/api/v5/repos/nope/nada").mock(return_value=Response(404, json={}))
    with pytest.raises(GiteeError) as exc:
        client.repo_details("nope", "nada")
    assert exc.value.error_type == "not_found"


@respx.mock
def test_readme_decodes_base64(client: GiteeClient):
    body = {"content": base64.b64encode("# Hello\n中文标题".encode()).decode()}
    respx.get("https://gitee.test/api/v5/repos/dromara/hutool/readme").mock(
        return_value=Response(200, json=body)
    )
    readme = client.repo_readme("dromara", "hutool")
    assert "# Hello" in readme
    assert "中文标题" in readme


@respx.mock
def test_repo_search_without_token_raises(client: GiteeClient):
    with pytest.raises(GiteeError) as exc:
        client.search_repositories("java")
    assert exc.value.error_type == "auth_required"


@respx.mock
def test_repo_search_with_token(client: GiteeClient):
    client.cfg.token = "fake-token"
    respx.get("https://gitee.test/api/v5/search/repositories").mock(
        return_value=Response(200, json={"total_count": 1, "items": [FAKE_REPO]})
    )
    total, items = client.search_repositories("hutool")
    assert total == 1
    assert items[0]["name"] == "hutool"


def test_activity_score_ranks_fresh_commits():
    now = time.time()
    fresh = [
        {
            "commit": {
                "committer": {"date": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now - 3600))}
            }
        }
    ]
    stale = [{"commit": {"committer": {"date": "2020-01-01T00:00:00"}}}]
    score_fresh = activity_score(FAKE_REPO, fresh)
    score_stale = activity_score(FAKE_REPO, stale)
    assert score_fresh > score_stale


def test_activity_score_bounded():
    score = activity_score(FAKE_REPO, FAKE_COMMITS)
    assert 0 < score <= 20


# ------------------------------------------------------------------ translate


def test_is_chinese():
    assert is_chinese("企业级微服务快速开发框架")
    assert not is_chinese("enterprise microservices framework")


def test_translator_gloss_fallback_when_provider_down():

    original = Translator()
    original._healthy = False
    original._last_check = time.time()
    result = original.zh_to_en("企业级微服务快速开发框架")
    assert result["translated"] is False
    assert "enterprise" in result["translation"]


def test_translator_glossary_terms():
    from gitee_mcp.translate import gloss

    assert "enterprise-grade" in gloss("企业级平台")
    assert "low-code" in gloss("低代码平台")


# ------------------------------------------------------------------ radar


@respx.mock
def test_humming_radar_uses_real_data_and_reports_dead_seeds():
    import gitee_mcp.client as client_mod
    import gitee_mcp.config as config

    old_client = client_mod._client
    old_base = config.settings.api_base
    old_seeds = config.settings.seed_repos
    config.settings.api_base = "https://gitee.test/api/v5"
    config.settings.seed_repos = ["dromara/hutool", "dead/seed"]
    client_mod._client = GiteeClient(config.settings)
    respx.get("https://gitee.test/api/v5/repos/dromara/hutool").mock(
        return_value=Response(200, json=FAKE_REPO)
    )
    respx.get("https://gitee.test/api/v5/repos/dromara/hutool/commits").mock(
        return_value=Response(200, json=FAKE_COMMITS)
    )
    respx.get("https://gitee.test/api/v5/repos/dead/seed").mock(return_value=Response(404, json={}))
    try:
        result = humming_radar(limit=5)
    finally:
        client_mod._client = old_client
        config.settings.api_base = old_base
        config.settings.seed_repos = old_seeds
    assert result["success"] is True
    assert result["data"]["dead_seeds"] == ["dead/seed"]
    assert len(result["data"]["repos"]) == 1
    assert result["data"]["repos"][0]["full_name"] == "dromara/hutool"


def test_enrich_normalizes_url_and_translation_flags():
    import gitee_mcp.config as config

    old_base = config.settings.llm_base_url
    config.settings.llm_base_url = "http://127.0.0.1:9/v1"  # unreachable
    try:
        out = _enrich(FAKE_REPO, translate=False)
        assert out["html_url"] == "https://gitee.com/dromara/hutool"
        assert out["need_translation"] is True
    finally:
        config.settings.llm_base_url = old_base
