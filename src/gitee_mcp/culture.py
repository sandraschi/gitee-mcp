"""Culture notes for Chinese OSS (F4).

Translation answers "what does this say"; culture notes answer "why does
this matter in the Chinese open-source world". explain() uses the local
LLM with a built-in fact sheet as context. When no provider is reachable
it returns the static fact sheet passages with an explicit note - never a
fabricated LLM claim.

The fact sheet is knowledge-sheet data (2026-08): it describes durable
structural facts about the Chinese OSS ecosystem, not live events, so it
does not go stale quickly. It is clearly labeled as the fallback source.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import settings
from .translate import translator

logger = logging.getLogger(__name__)

FACT_SHEET = """Facts about the Chinese open-source ecosystem (knowledge sheet):

- China's enterprise software world is dominated by a small set of "admin
  framework" families. RuoYi (若依) and its derivatives (RuoYi-Vue,
  RuoYi-Vue-Plus) are among the most-forked Java repos on Gitee; most
  Chinese back-office systems start from a RuoYi-like scaffold.
- The typical Chinese enterprise Java stack: Spring Boot + MyBatis(-Plus)
  + Redis + a Vue 2/3 admin UI (Element-UI / Element-Plus, Ant Design
  Vue, TDesign), Nacos for config/service discovery, xxl-job for
  scheduled jobs, Seata for distributed transactions, Dubbo for RPC.
- Vue (not React) is the dominant frontend framework in Chinese
  enterprises and Gitee; React is common but secondary.
- High-star Gitee projects are often full solutions rather than small
  libraries: mall/e-commerce suites, CMS/blog engines, low-code/visual
  builders (amis), and monolithic admin panels - reflecting the domestic
  freelance/agency and in-house enterprise market.
- Java is the largest language by enterprise adoption; Go is rising in
  ops/infra tooling; Rust is growing among enthusiasts. Kotlin and C#
  have smaller but real communities.
- OpenHarmony (华为) is a first-class platform on Gitee with its own
  ecosystem of devices/libraries.
- Most popular projects host on Gitee and mirror to GitHub or vice versa;
  some exist on Gitee only. Descriptions and docs are overwhelmingly
  Chinese.
- Gitee's "stars" skew lower than GitHub for the same project because the
  domestic audience is smaller - compare platforms before judging mass.
- License and compliance culture differs; many repos are MIT/Apache but
  some popular admin frameworks are GPL-family - check before reuse.
"""


def explain(topic: str) -> dict[str, Any]:
    """Explain a Chinese-OSS topic/term/repo via local LLM + fact sheet.

    Never fails hard: provider down -> labeled fact-sheet passages.
    """
    topic = (topic or "").strip()
    if not topic:
        return {"success": False, "note": "empty topic", "explanation": ""}
    health = translator.provider_health()
    if not health["available"]:
        return {
            "success": True,
            "explained": False,
            "explanation": FACT_SHEET,
            "note": (
                "Local LLM not reachable; returned the built-in fact sheet. "
                "Start Ollama or set GITEE_LLM_BASE_URL for a tailored answer."
            ),
            "source": "fact-sheet",
        }
    prompt = (
        "You are a guide to the Chinese open-source ecosystem. Using the fact "
        "sheet below and your own knowledge, explain the following topic in 3-5 "
        "concise sentences: what it is, why it matters in Chinese OSS, and one "
        "concrete example. Reply in English, plain text, no markdown.\n\n"
        f"Topic: {topic}\n\nFact sheet:\n{FACT_SHEET}"
    )
    try:
        resp = httpx.post(
            f"{settings.llm_base_url}/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a knowledgeable guide to Chinese open-source software.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 512,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        body = resp.json()
        content = (body["choices"][0]["message"]["content"] or "").strip()
        if not content:
            raise ValueError("empty completion")
        return {
            "success": True,
            "explained": True,
            "explanation": content,
            "model": settings.llm_model,
            "source": "local-llm",
        }
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Culture explain failed (%s) - using fact sheet", exc.__class__.__name__)
        return {
            "success": True,
            "explained": False,
            "explanation": FACT_SHEET,
            "note": f"LLM explain failed ({exc.__class__.__name__}); returned fact sheet.",
            "source": "fact-sheet",
        }
