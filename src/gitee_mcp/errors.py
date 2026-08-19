"""Shared tool helpers - error response factory and tool annotations.

Centralises the {success, message, error, error_type, suggestions} error
shape (TOOL_DESIGN_STANDARDS 4.2) with automatic logger.exception() capture,
and the FastMCP tool annotation constants (TOOL_DESIGN_STANDARDS 9).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Tool annotations: signal behavior to the agent (READ_ONLY / MUTATING / DESTRUCTIVE).
READ_ONLY: dict[str, Any] = {"readonly": True}
MUTATING: dict[str, Any] = {"readonly": False}
DESTRUCTIVE: dict[str, Any] = {"readonly": False, "destructive": True}


def error_response(
    exc: Exception,
    error_type: str = "error",
    suggestions: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a {success, message, error, error_type, suggestions} error dict.

    Must be called inside an except block so logger.exception() captures the
    active traceback. Never raises.
    """
    logger.exception("Tool failure (%s): %s", error_type, exc)
    return {
        "success": False,
        "message": str(exc),
        "error": str(exc),
        "error_type": error_type,
        "suggestions": suggestions or [],
        **extra,
    }
