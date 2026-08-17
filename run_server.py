"""PyInstaller / MCPB entry point - dual transport switch.

MCP_PORT (or PORT) set -> HTTP mode on 127.0.0.1:<port>; otherwise stdio.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gitee_mcp.server import main  # noqa: E402

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    sys.argv = ["run_server.py", "--mode", "http", "--host", host, "--port", str(port)]
else:
    sys.argv = ["run_server.py", "--mode", "stdio"]

main()
