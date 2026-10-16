"""Tool registry for the Campus Customs MCP server.

To add tools: create a module in this package that exposes plain functions
and lists them in a TOOLS tuple, then import it here and add it to
TOOL_MODULES. Tools in ADMIN_TOOL_NAMES are for the operator/backend only and
are filtered out of every agent's toolset.

Payment APPROVAL is deliberately not a tool. See mcp_server/approve.py.
"""

from __future__ import annotations

from fastmcp import FastMCP

from . import accounting, admin, board, facilities, inventory, orders, pricing, shop

TOOL_MODULES = (orders, facilities, pricing, shop, inventory, accounting, board, admin)
ADMIN_TOOL_NAMES = frozenset(fn.__name__ for fn in admin.TOOLS)


def register_all(mcp: FastMCP) -> None:
    for module in TOOL_MODULES:
        for fn in module.TOOLS:
            mcp.tool(fn)
