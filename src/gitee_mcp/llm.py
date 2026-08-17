"""Local LLM helpers for the Chat page - provider discovery and chat completion.

Local-first: probes Ollama (11434), LM Studio (1234) and the configured
GITEE_LLM_BASE_URL, then proxies chat completions to the selected provider.
"""

from __future__ import annotations

import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_PROVIDER_PROBES = [
    {
        "name": "ollama",
        "base": "http://127.0.0.1:11434/v1",
        "models_path": "/models",
        "port": 11434,
    },
    {
        "name": "lmstudio",
        "base": "http://127.0.0.1:1234/v1",
        "models_path": "/models",
        "port": 1234,
    },
]


def discover_providers() -> dict:
    providers = []
    for probe in _PROVIDER_PROBES:
        status = "probing"
        try:
            resp = httpx.get(probe["base"] + probe["models_path"], timeout=3.0)
            ok = resp.status_code == 200
            status = "detected" if ok else "not_found"
            if ok:
                providers.append({**probe, "status": status})
        except httpx.HTTPError:
            status = "not_found"
    # custom LLM base (GITEE_LLM_BASE_URL) is always offered when configured
    if settings.llm_configured:
        providers.append(
            {
                "name": "custom",
                "base": settings.llm_base_url,
                "models_path": "/models",
                "port": None,
                "status": "detected" if translator_healthy() else "not_found",
            }
        )
    return {
        "providers": providers,
        "selected_provider": "ollama"
        if any(p["name"] == "ollama" and p["status"] == "detected" for p in providers)
        else "",
        "default_model": settings.llm_model,
    }


def translator_healthy() -> bool:
    try:
        from .translate import translator

        return bool(translator.provider_health().get("available"))
    except Exception:
        return False


def chat_completion(messages: list[dict], model: str) -> dict:
    base = settings.llm_base_url
    target_model = model or settings.llm_model
    try:
        resp = httpx.post(
            f"{base}/chat/completions",
            json={"model": target_model, "messages": messages, "temperature": 0.6},
            timeout=120.0,
        )
        resp.raise_for_status()
        body = resp.json()
        return {
            "success": True,
            "message": body["choices"][0]["message"]["content"],
            "model": target_model,
        }
    except httpx.HTTPError as exc:
        logger.warning("Chat completion failed: %s", exc)
        return {
            "success": False,
            "error": f"LLM unreachable at {base} ({exc.__class__.__name__}). Start Ollama or configure GITEE_LLM_BASE_URL.",
            "error_type": "llm_unreachable",
        }
    except (KeyError, IndexError) as exc:
        logger.warning("Chat completion malformed: %s", exc)
        return {"success": False, "error": "Malformed LLM response", "error_type": "llm_malformed"}
