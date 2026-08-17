"""zh -> en translation via local LLM (Ollama, OpenAI-compatible).

Local-first doctrine: default endpoint is Ollama on 127.0.0.1:11434/v1.
No provider? Then translate() honestly reports untranslated rather than
faking a translation. A small built-in glossary still glosses common
Chinese OSS terms so summaries are readable even without an LLM.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Common Chinese OSS / repo terms (used only as a light gloss, not a real translation)
GLOSSARY = {
    "企业级": "enterprise-grade",
    "快速开发": "rapid development",
    "低代码": "low-code",
    "微服务": "microservices",
    "分布式": "distributed",
    "管理系统": "management system",
    "脚手架": "scaffold",
    "后台管理": "admin panel",
    "权限管理": "permission/authorization management",
    "多租户": "multi-tenant",
    "高并发": "high concurrency",
    "高性能": "high performance",
    "安全认证": "security authentication",
    "开源": "open source",
    "大数据": "big data",
    "人工智能": "artificial intelligence",
    "智能": "intelligent / smart",
    "实时": "real-time",
    "监控": "monitoring",
    "日志": "logging",
    "配置中心": "config center",
    "消息队列": "message queue",
    "接口文档": "API documentation",
    "自动生成": "auto-generation",
    "可视化": "visual",
    "工作流": "workflow",
    "低延迟": "low latency",
    "物联网": "Internet of Things (IoT)",
    "区块链": "blockchain",
    "前端": "frontend",
    "后端": "backend",
    "开发工具": "developer tool",
    "框架": "framework",
    "组件库": "component library",
    "开发平台": "development platform",
    "一站式": "all-in-one",
    "解决方案": "solution",
    "电商": "e-commerce",
    "支付": "payment",
    "社交": "social",
}

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def is_chinese(text: str) -> bool:
    """True when the text has a meaningful share of CJK characters."""
    if not text:
        return False
    cjk = len(_CJK_RE.findall(text))
    return cjk / max(len(text), 1) >= 0.15


def gloss(text: str) -> str:
    """Light dictionary gloss: replace known terms, flag what remains untranslated."""
    out = text
    for zh, en in sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(zh, f" {en} ")
    out = " ".join(out.split())  # collapse the spacing the CJK-free insertions left behind
    if _CJK_RE.search(out):
        out = f"{out} [partial gloss - set up Ollama for full translation]"
    return out


class Translator:
    def __init__(self) -> None:
        self._client: httpx.Client | None = None
        self._healthy: bool | None = None
        self._last_check: float = 0.0

    @property
    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def provider_health(self, force: bool = False) -> dict:
        now = time.time()
        if force or self._healthy is None or now - self._last_check > 60:
            self._last_check = now
            try:
                resp = self._http.get(f"{settings.llm_base_url}/models", timeout=5.0)
                self._healthy = resp.status_code == 200
            except httpx.HTTPError:
                self._healthy = False
        return {
            "available": bool(self._healthy),
            "base_url": settings.llm_base_url,
            "model": settings.llm_model,
        }

    def zh_to_en(self, text: str, max_chars: int = 1200) -> dict[str, Any]:
        """Translate Chinese text to English using the local LLM.

        Never fakes success: if the provider is down, returns the original
        text with translated=False and a recovery hint.
        """
        if not text or not text.strip():
            return {"translated": False, "translation": "", "note": "empty input"}
        health = self.provider_health()
        if not health["available"]:
            return {
                "translated": False,
                "translation": gloss(text[:max_chars]),
                "note": "Local LLM not reachable; gloss applied. Start Ollama "
                f"({settings.llm_base_url}) or set GITEE_LLM_BASE_URL.",
            }
        prompt = (
            "Translate the following Chinese text to natural, concise English. "
            "Reply with ONLY the translation, no quotes, no preamble.\n\n"
            f"{text[:max_chars]}"
        )
        try:
            resp = self._http.post(
                f"{settings.llm_base_url}/chat/completions",
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a translation engine. Output only the translated text, "
                            "nothing else - no explanations, no quotes, no markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024,
                },
                timeout=90.0,  # cold model loads can take a minute on CPU
            )
            resp.raise_for_status()
            body = resp.json()
            content = (body["choices"][0]["message"]["content"] or "").strip()
            if not content:
                raise ValueError("empty completion")
            return {"translated": True, "translation": content, "model": settings.llm_model}
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning("Translation failed: %s", exc)
            return {
                "translated": False,
                "translation": gloss(text[:max_chars]),
                "note": f"Translation failed ({exc.__class__.__name__}); gloss applied instead.",
            }


translator = Translator()
