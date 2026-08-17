"""Configuration for gitee-mcp.

Single source of truth for environment variables. One .env file at the repo
root is loaded when present; env vars always win (no multi-file fallback
chain - see fleet rule: one .env, one source of truth).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def _load_dotenv() -> None:
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"')


_load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


DEFAULT_SEED_REPOS = [
    "openharmony/openharmony",
    "RuoYi-Vue/RuoYi-Vue",
    "dromara/hutool",
    "dromara/sa-token",
    "dromara/RuoYi-Vue-Plus",
    "apache/dubbo",
    "seata/seata",
    "JPressProjects/jpress",
    "lyswhut/lx-music-desktop",
    "SnailClimb/JavaGuide",
    "macrozheng/mall",
    "xuxueli/xxl-job",
    "YunaiV/ruoyi-vue-pro",
    "alibaba/nacos",
    "spring-projects/spring-boot",
    "mybatis/mybatis-3",
    "apache/skywalking",
    "apache/shardingsphere",
    "apache/rocketmq",
    "doocs/advanced-java",
    "halo-dev/halo",
    "baomidou/mybatis-plus",
    "Tencent/APIJSON",
    "pandao/editor.md",
    "baidu/amis",
]


def _seed_repos() -> list[str]:
    raw = os.environ.get("GITEE_SEED_REPOS", "").strip()
    if not raw:
        return list(DEFAULT_SEED_REPOS)
    out = []
    for item in raw.split(","):
        item = item.strip()
        if item and "/" in item:
            out.append(item)
    return out or list(DEFAULT_SEED_REPOS)


@dataclass
class Settings:
    token: str = field(default_factory=lambda: os.environ.get("GITEE_TOKEN", "").strip())
    api_base: str = field(
        default_factory=lambda: os.environ.get("GITEE_API_BASE", "https://gitee.com/api/v5").rstrip(
            "/"
        )
    )
    webhook_secret: str = field(
        default_factory=lambda: os.environ.get("GITEE_WEBHOOK_SECRET", "").strip()
    )
    llm_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "GITEE_LLM_BASE_URL", "http://127.0.0.1:11434/v1"
        ).rstrip("/")
    )
    llm_model: str = field(
        default_factory=lambda: os.environ.get("GITEE_LLM_MODEL", "qwen2.5:7b").strip()
    )
    cache_ttl: int = field(default_factory=lambda: int(os.environ.get("GITEE_CACHE_TTL", "600")))
    backend_port: int = field(
        default_factory=lambda: int(os.environ.get("GITEE_BACKEND_PORT", "11161"))
    )
    frontend_port: int = field(
        default_factory=lambda: int(os.environ.get("GITEE_FRONTEND_PORT", "11162"))
    )
    seed_repos: list[str] = field(default_factory=_seed_repos)
    request_timeout: float = 15.0
    anonymous_rate_limit: int = 60

    @property
    def configured(self) -> bool:
        """True when a token is present (full tier)."""
        return bool(self.token)

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url) and bool(self.llm_model)


settings = Settings()
