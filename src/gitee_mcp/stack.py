"""Chinese-OSS tech-stack fingerprint (F2).

Detects the framework/ecosystem a repo belongs to by scanning the README
text and top-level contents names against a curated map of technologies
that dominate Chinese open source. Every detection carries a confidence
derived from hit density. The map is knowledge-sheet data (updated as the
ecosystem moves); hits are real string matches against the repo's own
text - nothing is fabricated.
"""

from __future__ import annotations

from typing import Any

# key -> (canonical label, aliases/keywords to match, family)
STACK_MAP: dict[str, tuple[str, tuple[str, ...], str]] = {
    "ruoyi": ("RuoYi", ("ruoyi", "若依"), "Java admin framework"),
    "spring_boot": ("Spring Boot", ("spring boot", "springboot", "spring-boot"), "Java"),
    "spring_cloud": (
        "Spring Cloud",
        ("spring cloud", "spring-cloud", "nacos", "gateway"),
        "Java microservices",
    ),
    "mybatis": (
        "MyBatis / MyBatis-Plus",
        ("mybatis", "mybatis-plus", "mybatisplus"),
        "Java persistence",
    ),
    "sa_token": ("Sa-Token", ("sa-token", "sa token"), "Java auth"),
    "hutool": ("Hutool", ("hutool", "糊涂工具"), "Java utilities"),
    "xxl_job": ("xxl-job", ("xxl-job", "xxljob"), "Java scheduling"),
    "seata": ("Seata", ("seata",), "Java distributed transactions"),
    "dubbo": ("Dubbo", ("dubbo",), "Java RPC"),
    "skywalking": ("Apache SkyWalking", ("skywalking",), "Java observability"),
    "vue2": ("Vue 2", ("vue2", "vue 2", "element-ui", "element ui", "vant2"), "Frontend"),
    "vue3": (
        "Vue 3",
        ("vue3", "vue 3", "element-plus", "element plus", "vite", "naive-ui"),
        "Frontend",
    ),
    "antd_vue": ("Ant Design Vue", ("ant-design-vue", "ant design vue"), "Frontend"),
    "tdesign": ("TDesign", ("tdesign",), "Frontend"),
    "uni_app": ("uni-app", ("uni-app", "uniapp"), "Cross-platform app"),
    "flutter": ("Flutter", ("flutter",), "Cross-platform app"),
    "electron": ("Electron", ("electron",), "Desktop"),
    "go": ("Go", ("golang", "go.mod", "gin", "gorm"), "Go"),
    "rust": ("Rust", ("rust", "cargo.toml", "tokio"), "Rust"),
    "python": ("Python", ("django", "flask", "fastapi", "pandas", "requirements.txt"), "Python"),
    "lowcode": (
        "Low-code platform",
        ("低代码", "low-code", "low code", "可视化搭建", "amis"),
        "Domain",
    ),
    "admin": (
        "Admin/RBAC platform",
        ("权限管理", "rbac", "后台管理", "管理系统", "admin"),
        "Domain",
    ),
    "iot": ("IoT", ("iot", "物联网", "mqtt"), "Domain"),
    "workflow": (
        "Workflow engine",
        ("workflow", "工作流", "flowable", "activiti", "camunda"),
        "Domain",
    ),
    "bigdata": ("Big data", ("大数据", "hadoop", "spark", "flink", "hive"), "Domain"),
    "ai_llm": ("AI / LLM", ("llm", "大模型", "ai", "openai", "rag", "langchain", "gpt"), "Domain"),
    "db": ("Database / ORM", ("数据库", "sqlite", "postgres", "mysql", "redis"), "Data"),
}

_FAMILIES = {
    "Java admin framework",
    "Java microservices",
    "Java persistence",
    "Java auth",
    "Java utilities",
    "Java scheduling",
    "Java distributed transactions",
    "Java RPC",
    "Java observability",
    "Frontend",
    "Cross-platform app",
    "Desktop",
    "Go",
    "Rust",
    "Python",
    "Domain",
    "Data",
}

_MAX_TEXT_CHARS = 60000


def _hits(text: str, keywords: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(1 for kw in keywords if kw in lowered)


def fingerprint(description: str, readme: str, contents: list[str]) -> dict[str, Any]:
    """Return {"technologies": [{key, label, family, confidence}],
    "dominant": str|None, "signals": int} from text scanning."""
    blob = " ".join(
        [
            description or "",
            readme[:_MAX_TEXT_CHARS] if readme else "",
            " ".join(contents[:200]),
        ]
    )
    found: dict[str, dict[str, Any]] = {}
    total_hits = 0
    for key, (label, keywords, family) in STACK_MAP.items():
        hits = _hits(blob, keywords)
        if hits == 0:
            continue
        total_hits += hits
        found[key] = {
            "key": key,
            "label": label,
            "family": family,
            "confidence": min(1.0, 0.35 + hits * 0.25),
            "hits": hits,
        }
    technologies = sorted(found.values(), key=lambda t: t["confidence"], reverse=True)
    dominant = technologies[0]["family"] if technologies else None
    return {
        "technologies": technologies,
        "dominant": dominant,
        "signals": total_hits,
        "note": (
            "Keyword scan of README + contents - a heuristic, not a build "
            "manifest. Empty result means no known Chinese-OSS stack marker "
            "was matched, not that the repo has no stack."
        ),
    }


def families() -> list[str]:
    return sorted(_FAMILIES)
