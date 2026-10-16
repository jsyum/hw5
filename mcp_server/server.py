"""Campus Customs MCP server.

Run from the project root (not yet wired to any agent or backend):

    python -m mcp_server.server

All tools operate on data/campus_customs_new.db only.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .tools import register_all

mcp = FastMCP(
    name="Campus Customs",
    instructions=(
        "Tools for the Campus Customs agent team. Every tool reads the working "
        "database data/campus_customs_new.db. Use desk.date_today (returned as "
        "shop_date) as the current date, never the real clock."
    ),
)

register_all(mcp)


if __name__ == "__main__":
    from .db import ensure_board_schema

    ensure_board_schema()
    mcp.run(show_banner=False)
