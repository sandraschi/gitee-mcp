"""gitee_translate portmanteau - Chinese to English translation via local LLM."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from ..server_state import mcp
from ..translate import is_chinese, translator


@mcp.tool(version="0.1.0")
async def gitee_translate(
    operation: Annotated[
        Literal["zh_to_en", "detect", "status"],
        Field(
            description=(
                "Operation: 'zh_to_en' translates Chinese text to English via the "
                "local LLM (honest fallback: dictionary gloss + untranslated flag "
                "when no provider is reachable); 'detect' reports whether text is "
                "Chinese; 'status' shows LLM provider health."
            )
        ),
    ],
    text: Annotated[str, Field(description="Text to translate or detect (max 1200 chars).")] = "",
    ctx: Context | None = None,
) -> dict:
    """Translate Chinese text to English - repo descriptions, issues, commit messages.

    [RATIONALE]
    The core value of a Gitee bridge for non-Chinese speakers is reading the
    ecosystem; translation belongs next to discovery in the tool surface.

    ## Return Format
    {"success": bool, "operation": str, "translated": bool, "translation": str,
    "note": str | null}

    ## Examples
    gitee_translate(operation="zh_to_en", text="企业级微服务快速开发框架")
    gitee_translate(operation="detect", text="hello world")
    gitee_translate(operation="status")
    """
    if operation == "status":
        health = translator.provider_health(force=True)
        return {
            "success": True,
            "operation": operation,
            "data": health,
            "message": "Local LLM reachable"
            if health["available"]
            else "Local LLM not reachable - gloss-only mode",
        }
    if operation == "detect":
        return {
            "success": True,
            "operation": operation,
            "text": text,
            "is_chinese": is_chinese(text),
            "message": "Contains significant Chinese text"
            if is_chinese(text)
            else "Not Chinese (or below threshold)",
        }
    if not text.strip():
        return {
            "success": False,
            "operation": operation,
            "error": "text is required for zh_to_en",
            "error_type": "validation",
        }
    result = translator.zh_to_en(text)
    return {
        "success": True,
        "operation": operation,
        "text": text,
        "translated": result.get("translated", False),
        "translation": result.get("translation", ""),
        "note": result.get("note"),
    }
