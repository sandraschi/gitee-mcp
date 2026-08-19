"""Tool registration for gitee-mcp.

Portmanteau imports - each module decorates @mcp.tool at import time, so
importing here during server boot is what actually registers the tools.
"""

from . import (  # noqa: F401
    corpus_tool,
    ecosystem_tool,
    explore,
    help_tool,
    prefab,
    repo,
    search,
    shutdown_tool,
    translate_tool,
    watchlist_tool,
    webhook_tool,
)
