"""Tool registration for gitee-mcp.

Portmanteau imports - each module decorates @mcp.tool at import time, so
importing here during server boot is what actually registers the tools.
"""

from . import explore, help_tool, prefab, repo, search, translate_tool, webhook_tool  # noqa: F401
