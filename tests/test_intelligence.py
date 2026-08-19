"""Tests for the v0.2 ecosystem-intelligence modules (history, stack,
search expansion, culture, watchlist, releases, feed, ecosystem, corpus).
No live network - respx doubles only.
"""

from __future__ import annotations

import time

import respx
from httpx import Response

from gitee_mcp import corpus, ecosystem, feed, history, release_notes, search_expand, stack
from gitee_mcp.culture import explain
from gitee_mcp.watchlist import add, check, list_entries, remove

# ------------------------------------------------------------------ history


def _write_history(rows: list[dict]):
    from gitee_mcp.config import DATA_DIR

    path = DATA_DIR / "radar_history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(__import__("json").dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_momentum_null_on_first_observation():
    _write_history([])
    mom = history.momentum_for("a/b", 5.0, 100, 50)
    assert mom["momentum"] is None
    assert mom["momentum_7d"] is None
    assert mom["surge"] is False


def test_momentum_deltas_and_surge():
    now = time.time()
    _write_history(
        [
            {
                "ts": now - 8 * 86400,
                "repo": "a/b",
                "activity_score": 2.0,
                "stargazers_count": 90,
                "forks_count": 40,
            },
            {
                "ts": now - 3600,
                "repo": "a/b",
                "activity_score": 6.0,
                "stargazers_count": 100,
                "forks_count": 50,
            },
        ]
    )
    mom = history.momentum_for("a/b", 6.0, 100, 50, now_ts=now)
    assert mom["momentum"] == 0.0  # same as previous (6.0)
    assert mom["momentum_7d"] == 4.0  # vs 7d-ago baseline 2.0
    assert mom["stars_delta_7d"] == 10
    assert mom["forks_delta_7d"] == 10


def test_surge_flag_when_delta_above_threshold():
    now = time.time()
    _write_history(
        [
            {
                "ts": now - 86400,
                "repo": "a/b",
                "activity_score": 2.0,
                "stargazers_count": 10,
                "forks_count": 5,
            }
        ]
    )
    mom = history.momentum_for("a/b", 7.0, 10, 5, now_ts=now)
    assert mom["momentum"] == 5.0
    assert mom["surge"] is True


def test_record_snapshot_then_star_history_and_movers():
    _write_history([])
    history.record_snapshot(
        [
            {"full_name": "a/b", "activity_score": 3.0, "stargazers_count": 10, "forks_count": 5},
            {"full_name": "c/d", "activity_score": 8.0, "stargazers_count": 20, "forks_count": 6},
        ]
    )
    time.sleep(0.01)
    history.record_snapshot(
        [
            {"full_name": "a/b", "activity_score": 5.0, "stargazers_count": 12, "forks_count": 6},
            {"full_name": "c/d", "activity_score": 7.0, "stargazers_count": 20, "forks_count": 6},
        ]
    )
    series = history.star_history("a/b")
    assert len(series) == 2
    assert series[0]["stargazers_count"] == 10
    assert series[-1]["stargazers_count"] == 12
    movers = history.top_movers(days=7)
    assert movers[0]["full_name"] == "a/b"
    assert movers[0]["delta"] == 2.0


# ------------------------------------------------------------------ stack


def test_stack_fingerprint_detects_ruoyi_vue():
    result = stack.fingerprint(
        "基于SpringBoot+MyBatis的权限管理系统",
        "RuoYi-Vue-Plus: spring boot admin framework with vue3 element-plus",
        ["pom.xml", "ruoyi-admin", "vue"],
    )
    assert result["dominant"]
    labels = {t["label"] for t in result["technologies"]}
    assert "RuoYi" in labels
    assert result["signals"] >= 1


def test_stack_fingerprint_empty_is_honest():
    result = stack.fingerprint("hello", "nothing to see", ["README.md"])
    assert result["technologies"] == []
    assert result["dominant"] is None
    assert "heuristic" in result["note"]


# ------------------------------------------------------------------ search expansion


def test_expand_query_maps_english_to_chinese():
    candidates = search_expand.expand_query("low-code platform", max_candidates=2)
    assert any("低代码" in c for c in candidates)


def test_expand_repos_query_appends_synonym():
    q = search_expand.expand_repos_query("iot framework")
    assert "框架" in q or "物联网" in q or "低代码" in q


def test_expand_repos_query_noop_for_unknown():
    assert search_expand.expand_repos_query("zzzqqqxyz") == "zzzqqqxyz"


# ------------------------------------------------------------------ culture


def test_culture_explain_fact_sheet_when_llm_down():
    from gitee_mcp.config import settings

    old_base = settings.llm_base_url
    settings.llm_base_url = "http://127.0.0.1:9/v1"
    try:
        result = explain("RuoYi")
        assert result["explained"] is False
        assert "facts about" in result["explanation"].lower()
        assert result["source"] == "fact-sheet"
    finally:
        settings.llm_base_url = old_base


# ------------------------------------------------------------------ watchlist


def test_watchlist_add_remove_list():
    entry = add("dromara/hutool", min_activity=8.0)
    assert entry.full_name == "dromara/hutool"
    entries = list_entries()
    assert len(entries) == 1
    assert entries[0].min_activity == 8.0
    assert remove("dromara/hutool") is True
    assert remove("dromara/hutool") is False
    assert list_entries() == []


@respx.mock
def test_watchlist_check_reports_changes():
    add("dromara/hutool")
    from gitee_mcp.client import GiteeClient
    from gitee_mcp.config import Settings

    cfg = Settings()
    cfg.token = ""
    cfg.api_base = "https://gitee.test/api/v5"
    client = GiteeClient(cfg)

    commit_url = "https://gitee.test/api/v5/repos/dromara/hutool/commits"
    respx.get(commit_url).mock(
        return_value=Response(
            200,
            json=[
                {"sha": "aaa", "commit": {"message": "one", "author": {"name": "x"}}},
                {"sha": "bbb", "commit": {"message": "two", "author": {"name": "x"}}},
            ],
        )
    )
    report = check(client)
    assert report["success"] is True
    assert report["count"] == 1
    assert report["entries"][0]["status"] in ("changed", "unchanged")

    # Second call with same shas -> unchanged
    report2 = check(client)
    assert report2["entries"][0]["status"] == "unchanged"


# ------------------------------------------------------------------ release notes


@respx.mock
def test_release_notes_fallback_no_llm():
    import gitee_mcp.client as client_mod
    from gitee_mcp.config import settings
    from gitee_mcp.translate import translator

    old_client = client_mod._client
    old_base = settings.llm_base_url
    cfg = type("Cfg", (), {"token": "", "api_base": "https://gitee.test/api/v5"})()
    client_mod._client = type(
        "C", (), {"cfg": cfg, "repo_releases": lambda self, o, r, limit=5: _FAKE_RELEASES[:limit]}
    )()
    settings.llm_base_url = "http://127.0.0.1:9/v1"
    translator._healthy = False
    translator._last_check = time.time()
    try:
        result = release_notes.summarize_latest("dromara", "hutool")
        assert result["has_releases"] is True
        assert result["translated"] is False
        assert "1.0.0" in str(result["releases"][0]["tag_name"])
    finally:
        client_mod._client = old_client
        settings.llm_base_url = old_base


_FAKE_RELEASES = [
    {
        "tag_name": "1.0.0",
        "name": "v1.0.0",
        "body": "新增企业级微服务支持",
        "published_at": "2026-08-01T00:00:00+08:00",
    }
]


# ------------------------------------------------------------------ feed


@respx.mock
def test_feed_builds_rss_from_radar():
    import gitee_mcp.client as client_mod
    import gitee_mcp.config as config

    old_client = client_mod._client
    old_base = config.settings.api_base
    old_seeds = config.settings.seed_repos
    config.settings.api_base = "https://gitee.test/api/v5"
    config.settings.seed_repos = ["dromara/hutool"]
    client_mod._client = type(
        "C",
        (),
        {
            "cfg": config.settings,
            "rate_limit_remaining": None,
            "repo_details": lambda self, o, r: _FAKE_REPO,
            "repo_commits": lambda self, o, r, limit=10: [],
        },
    )()
    try:
        xml = feed.build_feed(limit=5)
        assert '<rss version="2.0">' in xml
        assert "dromara/hutool" in xml
    finally:
        client_mod._client = old_client
        config.settings.api_base = old_base
        config.settings.seed_repos = old_seeds


_FAKE_REPO = {
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


# ------------------------------------------------------------------ ecosystem


@respx.mock
def test_ecosystem_graph_from_seeds():
    import gitee_mcp.client as client_mod
    import gitee_mcp.config as config

    old_client = client_mod._client
    old_seeds = config.settings.seed_repos
    config.settings.seed_repos = ["dromara/hutool", "dromara/sa-token"]
    client_mod._client = type(
        "C",
        (),
        {
            "cfg": config.settings,
            "rate_limit_remaining": None,
            "repo_details": lambda self, o, r: {
                **_FAKE_REPO,
                "full_name": f"{o}/{r}",
                "parent": None,
                "fork": False,
            },
        },
    )()
    try:
        graph = ecosystem.build_graph(scope="seeds")
        assert graph["success"] is True
        assert "dromara" in [n["id"] for n in graph["nodes"]]
        assert graph["counts"]["edges"] == 2
    finally:
        client_mod._client = old_client
        config.settings.seed_repos = old_seeds


@respx.mock
def test_ecosystem_mirror_found_and_not_found():
    import gitee_mcp.client as client_mod
    from gitee_mcp.config import settings

    old_client = client_mod._client
    old_base = settings.api_base
    settings.api_base = "https://gitee.test/api/v5"
    client_mod._client = type(
        "C",
        (),
        {
            "cfg": settings,
            "rate_limit_remaining": None,
            "repo_details": lambda self, o, r: _FAKE_REPO,
        },
    )()
    try:
        respx.get("https://api.github.com/repos/dromara/hutool").mock(
            return_value=Response(
                200,
                json={
                    "stargazers_count": 30000,
                    "forks_count": 12000,
                    "pushed_at": "2026-08-10T00:00:00Z",
                    "description": "Java tools",
                    "language": "Java",
                    "html_url": "https://github.com/dromara/hutool",
                },
            )
        )
        result = ecosystem.mirror_compare("dromara", "hutool")
        assert result["on_github"] is True
        assert result["delta"]["stars"] == -7000

        respx.get("https://api.github.com/repos/gitee/only").mock(
            return_value=Response(404, json={})
        )
        result2 = ecosystem.mirror_compare("gitee", "only")
        assert result2["on_github"] is False
        assert "not found on GitHub" in result2["note"]
    finally:
        client_mod._client = old_client
        settings.api_base = old_base


def test_ecosystem_digest_empty_history_is_honest():
    result = ecosystem.weekly_digest(days=7, write_file=False)
    assert result["success"] is True
    assert "Not enough history" in result["narrative"]


# ------------------------------------------------------------------ corpus


def test_corpus_ingest_and_search():
    corpus.ingest("dromara/hutool", "企业级Java工具类库 with 低代码 and 权限管理 features")
    corpus.ingest("apache/dubbo", "distributed RPC framework for microservices")
    hits = corpus.search("权限管理")
    assert any(h["full_name"] == "dromara/hutool" for h in hits)
    hits2 = corpus.search("microservices")
    assert any(h["full_name"] == "apache/dubbo" for h in hits2)
    assert corpus.count() == 2
    assert "dromara/hutool" in corpus.list_indexed()
