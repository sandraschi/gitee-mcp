"""gitee_shutdown - self-termination tool for the gitee-mcp server."""

from __future__ import annotations

import os
import threading
import time

from fastmcp import Context

from ..errors import DESTRUCTIVE
from ..server_state import mcp


@mcp.tool(annotations=DESTRUCTIVE, version="0.1.0")
async def gitee_shutdown(confirm: bool = False, ctx: Context | None = None) -> dict:
    """Gracefully stop the gitee-mcp server process.

    [RATIONALE]
    Agents and operators need a sanctioned way to stop a long-running HTTP
    server without taskkilling it by hand. This tool exits the process after
    a short delay so the in-flight response can flush.

    ## Return Format
    {"success": bool, "message": str}

    ## Examples
    gitee_shutdown(confirm=True)
    """
    if not confirm:
        return {
            "success": False,
            "message": "Confirmation required - call gitee_shutdown(confirm=True) to stop the server.",
        }

    def _exit() -> None:
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=_exit, daemon=True).start()
    return {"success": True, "message": "gitee-mcp shutting down now."}
