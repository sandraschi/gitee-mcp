"""gitee-mcp server - FastMCP instance, FastAPI REST surface, dual transport.

Run modes:
  stdio : uv run python -m gitee_mcp.server          (no env vars)
  http  : uv run python -m gitee_mcp.server --mode http --host 127.0.0.1 --port 11161
  auto  : run_server.py switches on MCP_PORT / PORT env
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import time
from collections import deque
from pathlib import Path

import uvicorn
from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import __version__
from .client import get_client
from .config import settings
from .radar import humming_radar
from .server_state import mcp
from .translate import translator

logger = logging.getLogger("gitee_mcp")

# ------------------------------------------------------------------ log ring


class RingBufferHandler(logging.Handler):
    """In-memory ring buffer so the webapp Logs page works without files."""

    def __init__(self, capacity: int = 500) -> None:
        super().__init__()
        self.capacity = capacity
        self.records: deque[dict] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        # logging must never raise; the ring buffer is best-effort
        with contextlib.suppress(Exception):
            self.records.append(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
                    "level": record.levelname,
                    "source": record.name,
                    "message": record.getMessage(),
                }
            )


_ring = RingBufferHandler()
logging.basicConfig(
    level=logging.INFO, handlers=[_ring], format="%(levelname)s %(name)s: %(message)s"
)

# ------------------------------------------------------------------ MCP app

from . import tools as _tools  # noqa: E402, F401  (side-effect: registers all @mcp.tool)


async def _discover_tool_names() -> list[str]:
    try:
        tools = await mcp.list_tools()
        return sorted(t.name for t in tools)
    except Exception:
        return []


_TOOL_NAMES: list[str] = asyncio.run(_discover_tool_names())
_TOOL_COUNT = len(_TOOL_NAMES)


@mcp.resource("skill://gitee-expert/SKILL.md")
def skill_gitee_expert() -> str:
    """The gitee-expert skill - how to use the server well."""
    skill_path = Path(__file__).parent / "skills" / "gitee-expert" / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return "Gitee MCP server skill: use gitee_explore for discovery, gitee_repo for intel, gitee_translate for zh->en."


@mcp.prompt()
def gitee_research() -> str:
    """Discover what is humming on Gitee, profile a repo, and translate it to English."""
    return (
        "You are exploring the Chinese open-source ecosystem on Gitee.\n"
        "1. Call gitee_explore(operation='humming', limit=10) to see what is active right now.\n"
        "2. Pick a repo that looks interesting and call gitee_repo(operation='details', owner=..., repo=...), "
        "then gitee_repo(operation='readme', ...) for its README.\n"
        "3. If a description or README is in Chinese, call gitee_translate(operation='zh_to_en', text=...) "
        "to gloss it via the local LLM (or the built-in glossary).\n"
        "4. Prefer the anonymized anonymous tier and respect the ~60 requests/hour budget - "
        "cache results and do not re-fetch the same repo twice in a session."
    )


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"


class ChatRequest(BaseModel):
    messages: list[dict]
    model: str = ""


# ------------------------------------------------------------------ REST app


def build_app() -> FastAPI:
    _mcp_http = mcp.http_app(path="/")
    app = FastAPI(title="Gitee MCP", version=__version__, lifespan=_mcp_http.lifespan)

    # Fleet CORS standard: explicit origins + unconditional LAN/Tailscale regex.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{settings.frontend_port}",
            f"http://127.0.0.1:{settings.frontend_port}",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=(
            r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost"
            r"|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            r"|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/mcp", _mcp_http)

    @app.get("/api/health")
    def health() -> dict:
        client = get_client()
        snapshot = client.status_snapshot()
        return {
            "status": "ok",
            "server": "gitee-mcp",
            "version": __version__,
            "uptime_seconds": int(time.time() - _START_TS),
            "tool_count": _TOOL_COUNT,
            "configured": settings.configured,
            "tier": snapshot["tier"],
            "providers": {
                "gitee": {"tier": snapshot["tier"], "configured": settings.configured},
                "llm": translator.provider_health(),
            },
        }

    @app.get("/api/v1/diagnostics")
    def diagnostics() -> dict:
        return {
            "status": "ok",
            "server": "gitee-mcp",
            "version": __version__,
            "uptime_seconds": int(time.time() - _START_TS),
            "tool_count": _TOOL_COUNT,
            "tools": [{"name": name} for name in sorted(_tool_names())],
            "system": {"windows": os.name == "nt"},
            "errors": [],
        }

    @app.get("/api/capabilities")
    def capabilities() -> dict:
        return {
            "server": "gitee-mcp",
            "version": __version__,
            "features": {
                "search": settings.configured or None,
                "translate": True,
                "webhooks": True,
                "anonymous": True,
            },
        }

    @app.get("/api/tools")
    def tools_list() -> dict:
        return {"tools": sorted(_tool_names())}

    @app.get("/api/skills")
    def skills_list() -> dict:
        return {
            "skills": [
                {
                    "name": "gitee-expert",
                    "uri": "skill://gitee-expert/SKILL.md",
                    "description": "How to use gitee-mcp well - discovery, intel, translation.",
                }
            ]
        }

    @app.get("/api/skills/{name}")
    def skill_content(name: str) -> str:
        skill_path = Path(__file__).parent / "skills" / f"{name}" / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return "not found"

    @app.get("/api/dashboard")
    def dashboard() -> dict:
        client = get_client()
        snapshot = client.status_snapshot()
        return {
            "server": "gitee-mcp",
            "version": __version__,
            "uptime_seconds": int(time.time() - _START_TS),
            "tool_count": _TOOL_COUNT,
            "configured": settings.configured,
            "tier": snapshot["tier"],
            "rate_limit": {
                "remaining": snapshot["rate_limit_remaining"],
                "total": snapshot["rate_limit_total"],
            },
            "seed_count": len(settings.seed_repos),
            "llm": translator.provider_health(),
        }

    @app.get("/api/explore/humming")
    def explore_humming(limit: int = 20, language: str = "", translate: bool = False) -> dict:
        return humming_radar(limit=limit, language=language, translate=translate)

    @app.get("/api/repos/{owner}/{repo}/{surface}", response_model=None)
    def repo_surface(
        owner: str, repo: str, surface: str, path: str = "", limit: int = 10
    ) -> dict | JSONResponse:
        from .tools.repo import gitee_repo

        if surface not in ("details", "readme", "languages", "commits", "contents", "branches"):
            return JSONResponse(
                {"success": False, "error": f"unknown surface {surface}"}, status_code=400
            )
        return asyncio.run(
            gitee_repo(operation=surface, owner=owner, repo=repo, path=path, limit=limit)
        )

    @app.get("/api/search/{surface}", response_model=None)
    def search_surface(surface: str, q: str = "", limit: int = 10) -> dict | JSONResponse:
        from .tools.search import gitee_search

        if surface == "users":
            return asyncio.run(gitee_search(operation="users", query=q, limit=limit))
        if surface == "repos":
            return asyncio.run(gitee_search(operation="repos", query=q, limit=limit))
        return JSONResponse(
            {"success": False, "error": f"unknown surface {surface}"}, status_code=400
        )

    @app.post("/api/translate", response_model=None)
    def translate_route(req: TranslateRequest = Body(...)) -> dict | JSONResponse:  # noqa: B008
        if req.target_lang != "en":
            return JSONResponse(
                {
                    "success": False,
                    "error": "only en target supported for now",
                    "error_type": "validation",
                },
                status_code=400,
            )
        return asyncio.run(_translate_call(req.text))

    @app.get("/api/translate/status")
    def translate_status() -> dict:
        return {"success": True, "data": translator.provider_health(force=True)}

    @app.post("/api/webhooks/gitee", response_model=None)
    async def webhook_receive(request: Request) -> dict | JSONResponse:
        from .tools.webhook_tool import append_event

        headers = dict(request.headers)
        secret = headers.get("x-gitee-token", "")
        if settings.webhook_secret and secret != settings.webhook_secret:
            return JSONResponse(
                {"success": False, "error": "invalid webhook secret"}, status_code=403
            )
        try:
            payload = await request.json()
        except Exception:
            payload = {"raw": (await request.body()).decode("utf-8", errors="replace")[:4000]}
        event_id = append_event(payload, headers)
        logger.info("Webhook %s received (%s)", headers.get("x-gitee-event", "unknown"), event_id)
        return {"success": True, "id": event_id}

    @app.get("/api/webhooks/events")
    def webhook_events(limit: int = 20) -> dict:
        from .tools.webhook_tool import list_events

        events = list_events(limit)
        return {"success": True, "events": events, "count": len(events)}

    @app.delete("/api/webhooks/events")
    def webhook_events_clear() -> dict:
        from .tools.webhook_tool import clear_events

        cleared = clear_events()
        return {"success": True, "cleared": cleared}

    @app.get("/api/logs")
    def logs(limit: int = 100, level: str = "") -> dict:
        records = list(_ring.records)
        if level:
            records = [r for r in records if r["level"] == level.upper()]
        return {"logs": records[-max(limit, 1) :], "count": len(records)}

    @app.post("/api/shutdown", response_model=None)
    def shutdown() -> dict:
        """Graceful self-termination - stops the uvicorn server process."""
        import threading

        def _exit() -> None:
            time.sleep(0.5)
            import os

            os._exit(0)

        threading.Thread(target=_exit, daemon=True).start()
        return {"success": True, "message": "gitee-mcp shutting down now."}

    @app.get("/api/llm/discover")
    def llm_discover() -> dict:
        from .llm import discover_providers

        return discover_providers()

    @app.get("/api/llm/providers")
    def llm_providers() -> dict:
        from .llm import discover_providers

        return discover_providers()

    @app.post("/api/llm/chat")
    def llm_chat(req: ChatRequest = Body(...)) -> dict:  # noqa: B008
        from .llm import chat_completion

        return chat_completion(req.messages, req.model or settings.llm_model)

    return app


async def _translate_call(text: str) -> dict:
    result = translator.zh_to_en(text)
    return {
        "success": True,
        "translated": result.get("translated", False),
        "translation": result.get("translation", ""),
        "note": result.get("note"),
    }


def _tool_names() -> list[str]:
    return _TOOL_NAMES


_START_TS = time.time()
app = build_app()


# ------------------------------------------------------------------- entry


def main() -> None:
    parser = argparse.ArgumentParser(prog="gitee-mcp")
    parser.add_argument("--mode", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=settings.backend_port)
    args = parser.parse_args()

    if args.mode == "http":
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
