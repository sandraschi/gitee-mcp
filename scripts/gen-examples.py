"""Generate assets/prompts/examples.json (100+ curated tool-call examples).

Run: uv run python scripts/gen-examples.py
The output is committed - this script exists so the artifact stays
reproducible and auditable.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "prompts" / "examples.json"

E = []


def add(name: str, description: str, prompt: str, tool: str, arguments: dict) -> None:
    E.append(
        {
            "name": name,
            "description": description,
            "prompt": prompt,
            "tool": tool,
            "arguments": arguments,
        }
    )


# ---------------------------------------------------------------- gitee_explore
explore_prompts = [
    ("radar-default", "What is humming on Gitee right now?", {}),
    ("radar-ten", "Show the 10 most active repos on Gitee.", {"limit": 10}),
    ("radar-twenty-five", "Give me the top 25 humming repos on Gitee.", {"limit": 25}),
    ("radar-python", "Which Python projects are humming on Gitee?", {"language": "Python"}),
    ("radar-java", "Show me the most active Java repos on Gitee.", {"language": "Java"}),
    ("radar-go", "What is hot in Go on Gitee?", {"language": "Go"}),
    ("radar-rust", "Any Rust repos humming on Gitee?", {"language": "Rust"}),
    ("radar-ts", "Which TypeScript projects are active on Gitee?", {"language": "TypeScript"}),
    (
        "radar-translated",
        "Show the humming radar and translate the descriptions.",
        {"translate": True},
    ),
    (
        "radar-translated-five",
        "Translate the top 5 Chinese repo descriptions on Gitee.",
        {"limit": 5, "translate": True},
    ),
    ("radar-recommended", "What are the recommended seed repos?", {"operation": "recommended"}),
    ("radar-refresh", "Refresh the Gitee radar seed list.", {"operation": "refresh"}),
    (
        "radar-top-starred",
        "What are the top 15 most starred repos on Gitee?",
        {"operation": "top_starred", "limit": 15},
    ),
    (
        "radar-top-forked",
        "Show the most forked repos on Gitee.",
        {"operation": "top_forked", "limit": 10},
    ),
    ("radar-small", "Just the top 3 repos on Gitee right now.", {"limit": 3}),
    ("radar-vue", "Is anything Vue-related humming on Gitee?", {"language": "Vue"}),
]
for name, prompt, args in explore_prompts:
    op = args.get("operation", "humming")
    add(
        f"explore-{name}",
        f"gitee_explore {op} ({prompt[:60]})",
        prompt,
        "gitee_explore",
        {"operation": op, **args},
    )

# ---------------------------------------------------------------- gitee_repo
repo_cases = [
    ("hutool-details", "Profile dromara/hutool.", "dromara", "hutool", "details", {}),
    (
        "mall-details",
        "Give me a full profile of macrozheng/mall.",
        "macrozheng",
        "mall",
        "details",
        {},
    ),
    (
        "xxl-job-details",
        "What can you tell me about xuxueli/xxl-job?",
        "xuxueli",
        "xxl-job",
        "details",
        {},
    ),
    (
        "JavaGuide-details",
        "Profile SnailClimb/JavaGuide.",
        "SnailClimb",
        "JavaGuide",
        "details",
        {},
    ),
    ("dubbo-details", "Show details of apache/dubbo.", "apache", "dubbo", "details", {}),
    ("seata-details", "What is seata/seata?", "seata", "seata", "details", {}),
    ("nacos-details", "Profile alibaba/nacos.", "alibaba", "nacos", "details", {}),
    ("halo-details", "Tell me about halo-dev/halo.", "halo-dev", "halo", "details", {}),
    (
        "lx-music-details",
        "What is lyswhut/lx-music-desktop?",
        "lyswhut",
        "lx-music-desktop",
        "details",
        {},
    ),
    (
        "openharmony-details",
        "Profile openharmony/openharmony.",
        "openharmony",
        "openharmony",
        "details",
        {},
    ),
    (
        "ruoyi-details",
        "Show details of RuoYi-Vue/RuoYi-Vue.",
        "RuoYi-Vue",
        "RuoYi-Vue",
        "details",
        {},
    ),
    (
        "mybatis-plus-details",
        "Profile baomidou/mybatis-plus.",
        "baomidou",
        "mybatis-plus",
        "details",
        {},
    ),
    ("skywalking-details", "What is apache/skywalking?", "apache", "skywalking", "details", {}),
    (
        "shardingsphere-details",
        "Show details of apache/shardingsphere.",
        "apache",
        "shardingsphere",
        "details",
        {},
    ),
    ("rocketmq-details", "Profile apache/rocketmq.", "apache", "rocketmq", "details", {}),
    (
        "advanced-java-details",
        "What is doocs/advanced-java?",
        "doocs",
        "advanced-java",
        "details",
        {},
    ),
    ("jpress-details", "Profile JPressProjects/jpress.", "JPressProjects", "jpress", "details", {}),
    ("amis-details", "What is baidu/amis?", "baidu", "amis", "details", {}),
    (
        "editor-md-details",
        "Show details of pandao/editor.md.",
        "pandao",
        "editor.md",
        "details",
        {},
    ),
    ("sa-token-details", "Profile dromara/sa-token.", "dromara", "sa-token", "details", {}),
    ("hutool-readme", "Summarize the README of dromara/hutool.", "dromara", "hutool", "readme", {}),
    (
        "mall-readme",
        "What does the macrozheng/mall README say?",
        "macrozheng",
        "mall",
        "readme",
        {},
    ),
    (
        "JavaGuide-readme",
        "Summarize SnailClimb/JavaGuide README for me.",
        "SnailClimb",
        "JavaGuide",
        "readme",
        {},
    ),
    (
        "ruoyi-readme",
        "Read the README of RuoYi-Vue/RuoYi-Vue.",
        "RuoYi-Vue",
        "RuoYi-Vue",
        "readme",
        {},
    ),
    (
        "dubbo-readme",
        "Show me the apache/dubbo README highlights.",
        "apache",
        "dubbo",
        "readme",
        {},
    ),
    ("hutool-langs", "Language breakdown of dromara/hutool?", "dromara", "hutool", "languages", {}),
    ("mall-langs", "Which languages in macrozheng/mall?", "macrozheng", "mall", "languages", {}),
    (
        "openharmony-langs",
        "Language mix of openharmony/openharmony.",
        "openharmony",
        "openharmony",
        "languages",
        {},
    ),
    ("seata-langs", "Languages used in seata/seata.", "seata", "seata", "languages", {}),
    (
        "hutool-commits",
        "Recent commits in dromara/hutool.",
        "dromara",
        "hutool",
        "commits",
        {"limit": 10},
    ),
    (
        "xxl-job-commits",
        "Last 5 commits in xuxueli/xxl-job.",
        "xuxueli",
        "xxl-job",
        "commits",
        {"limit": 5},
    ),
    (
        "skywalking-commits",
        "What did apache/skywalking commit recently?",
        "apache",
        "skywalking",
        "commits",
        {"limit": 8},
    ),
    (
        "mall-commits",
        "Show the 3 newest commits in macrozheng/mall.",
        "macrozheng",
        "mall",
        "commits",
        {"limit": 3},
    ),
    ("hutool-contents", "Top-level files of dromara/hutool.", "dromara", "hutool", "contents", {}),
    (
        "advanced-java-contents",
        "List docs folder of doocs/advanced-java.",
        "doocs",
        "advanced-java",
        "contents",
        {"path": "docs"},
    ),
    (
        "ruoyi-contents",
        "What is in the root of YunaiV/ruoyi-vue-pro?",
        "YunaiV",
        "ruoyi-vue-pro",
        "contents",
        {},
    ),
    ("dubbo-branches", "Branches of apache/dubbo.", "apache", "dubbo", "branches", {}),
    (
        "nacos-branches",
        "Which branches does alibaba/nacos have?",
        "alibaba",
        "nacos",
        "branches",
        {},
    ),
    (
        "hutool-commits-20",
        "20 recent commits in dromara/hutool.",
        "dromara",
        "hutool",
        "commits",
        {"limit": 20},
    ),
    ("editor-md-contents", "Contents of pandao/editor.md.", "pandao", "editor.md", "contents", {}),
    ("amis-langs", "Language mix of baidu/amis.", "baidu", "amis", "languages", {}),
    ("rocketmq-readme", "README summary of apache/rocketmq.", "apache", "rocketmq", "readme", {}),
    (
        "mybatis-plus-details",
        "Profile baomidou/mybatis-plus again with license info.",
        "baomidou",
        "mybatis-plus",
        "details",
        {},
    ),
    (
        "sa-token-commits",
        "Recent commits in dromara/sa-token.",
        "dromara",
        "sa-token",
        "commits",
        {"limit": 6},
    ),
    (
        "halo-commits",
        "What has halo-dev/halo committed lately?",
        "halo-dev",
        "halo",
        "commits",
        {"limit": 5},
    ),
    (
        "advanced-java-readme",
        "Summarize doocs/advanced-java README.",
        "doocs",
        "advanced-java",
        "readme",
        {},
    ),
    (
        "skywalking-langs",
        "Language breakdown of apache/skywalking.",
        "apache",
        "skywalking",
        "languages",
        {},
    ),
]
for name, prompt, owner, repo, surface, extra in repo_cases:
    add(
        f"repo-{name}",
        f"gitee_repo {surface} {owner}/{repo}",
        prompt,
        "gitee_repo",
        {"operation": surface, "owner": owner, "repo": repo, **extra},
    )

# ---------------------------------------------------------------- gitee_search
search_cases = [
    ("users-sandra", "Find the Gitee user 'sandra'.", "users", "sandra", {}),
    ("users-macrozheng", "Search Gitee for user macrozheng.", "users", "macrozheng", {}),
    ("users-jackson", "Find users named Jackson on Gitee.", "users", "jackson", {}),
    ("users-hutool", "Is there a Gitee user called hutool?", "users", "hutool", {}),
    ("users-openharmony", "Find the openharmony organization account.", "users", "openharmony", {}),
    (
        "repos-lowcode",
        "Search Gitee repos for low code platforms.",
        "repos",
        "low code",
        {"sort": "stargazers_count"},
    ),
    ("repos-vue3", "Find Vue 3 admin frameworks on Gitee.", "repos", "vue3 admin", {}),
    ("repos-fastmcp", "Is fastmcp available on Gitee?", "repos", "fastmcp", {}),
    (
        "repos-ml",
        "Search Gitee for machine learning projects.",
        "repos",
        "machine learning",
        {"sort": "forks_count"},
    ),
    ("repos-chatgpt", "Gitee repos about ChatGPT.", "repos", "chatgpt", {"sort": "updated"}),
    ("repos-springboot", "SpringBoot starter projects on Gitee.", "repos", "springboot", {}),
    (
        "repos-iot",
        "IoT platforms hosted on Gitee.",
        "repos",
        "物联网",
        {"sort": "stargazers_count"},
    ),
    ("repos-admin", "Admin dashboards on Gitee.", "repos", "admin", {}),
    (
        "repos-whatsnew",
        "Recently updated repos about RAG on Gitee.",
        "repos",
        "rag",
        {"sort": "pushed"},
    ),
    ("repos-kotlin", "Kotlin projects on Gitee.", "repos", "kotlin", {}),
    (
        "user-repos-macrozheng",
        "Public repos of macrozheng.",
        "user_repos",
        "",
        {"login": "macrozheng"},
    ),
    (
        "user-repos-snailclimb",
        "What repos does SnailClimb have?",
        "user_repos",
        "",
        {"login": "SnailClimb"},
    ),
    ("user-repos-lyswhut", "List lyswhut's public repos.", "user_repos", "", {"login": "lyswhut"}),
    ("user-repos-yunaiv", "Repos by YunaiV on Gitee.", "user_repos", "", {"login": "YunaiV"}),
]
for name, prompt, surface, query, extra in search_cases:
    add(
        f"search-{name}",
        f"gitee_search {surface} ({prompt[:60]})",
        prompt,
        "gitee_search",
        {"operation": surface, "query": query, **extra},
    )

# ---------------------------------------------------------------- gitee_translate
translations = [
    ("企业级微服务快速开发框架", "enterprise microservices framework"),
    ("一套基于SpringBoot+MyBatis的电商系统", "SpringBoot+MyBatis e-commerce system"),
    ("高性能分布式缓存系统", "high performance distributed cache"),
    ("低代码开发平台，拖拽式生成管理后台", "low-code platform with drag-and-drop admin generation"),
    ("开源物联网平台，支持设备接入与管理", "open-source IoT platform with device management"),
    ("安全认证框架，支持多租户与OAuth2", "auth framework with multi-tenant and OAuth2"),
    ("轻量级任务调度平台", "lightweight job scheduling platform"),
    ("一站式 DevOps 平台", "all-in-one DevOps platform"),
    ("接口文档自动生成工具", "automatic API documentation generator"),
    ("在线代码托管平台", "online code hosting platform"),
    ("分布式事务解决方案", "distributed transaction solution"),
    ("智能运维监控告警系统", "intelligent ops monitoring and alerting system"),
    ("实时消息推送服务", "real-time message push service"),
    ("基于大模型的智能问答助手", "LLM-based intelligent Q&A assistant"),
    ("前后端分离的后台管理系统", "frontend-backend separated admin system"),
    ("快速构建微服务的脚手架", "microservice scaffolding for rapid development"),
    ("企业级工作流引擎", "enterprise workflow engine"),
    ("可视化数据大屏", "visual data dashboard"),
    ("高并发秒杀系统示例", "high-concurrency flash-sale example"),
    ("容器编排与管理平台", "container orchestration and management platform"),
]
for i, (zh, gloss) in enumerate(translations):
    add(
        f"translate-zh-{i:02d}",
        f"Translate Chinese OSS term: {gloss}",
        f"Translate this to English: {zh}",
        "gitee_translate",
        {"operation": "zh_to_en", "text": zh},
    )
add(
    "translate-generic",
    "Translate a Chinese repo description",
    "Translate this repo description to English: 一套基于微服务的电商中台系统",
    "gitee_translate",
    {"operation": "zh_to_en", "text": "一套基于微服务的电商中台系统"},
)
add(
    "translate-detect-zh",
    "Detect Chinese text",
    "Does this contain Chinese: 高并发分布式系统?",
    "gitee_translate",
    {"operation": "detect", "text": "高并发分布式系统"},
)
add(
    "translate-detect-en",
    "Detect English text",
    "Is 'microservices framework' Chinese?",
    "gitee_translate",
    {"operation": "detect", "text": "microservices framework"},
)
add(
    "translate-status",
    "Translation provider status",
    "Is the translation service up?",
    "gitee_translate",
    {"operation": "status"},
)

# ---------------------------------------------------------------- gitee_webhook
add(
    "webhook-list",
    "List recent webhook events",
    "What webhook events came in recently?",
    "gitee_webhook",
    {"operation": "list", "limit": 20},
)
add(
    "webhook-list-5",
    "Last 5 webhook events",
    "Show the last 5 webhook events.",
    "gitee_webhook",
    {"operation": "list", "limit": 5},
)
add(
    "webhook-clear",
    "Clear webhook history",
    "Clear the webhook event history.",
    "gitee_webhook",
    {"operation": "clear"},
)

# ---------------------------------------------------------------- prefab cards
add(
    "card-humming",
    "Humming radar as a card",
    "Show the Gitee humming radar card.",
    "show_gitee_humming_card",
    {"limit": 8},
)
add(
    "card-humming-translate",
    "Humming radar card with translations",
    "Show the top 5 Gitee repos as a card, translated.",
    "show_gitee_humming_card",
    {"limit": 5, "translate": True},
)
add(
    "card-status",
    "Server status card",
    "Show the gitee-mcp status card.",
    "show_gitee_status_card",
    {},
)

# ---------------------------------------------------------------- help
add("help-overview", "Server help", "What can you do with Gitee?", "gitee_help", {})

assert len(E) >= 100, f"only {len(E)} examples - need 100+"
OUT.write_text(json.dumps(E, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(E)} examples to {OUT}")
