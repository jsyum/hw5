"""The backend's only route to shop data: the Campus Customs MCP server.

The backend never opens the database itself. It launches mcp_server over
stdio and gives each agent a filtered view of its tools.
"""

from __future__ import annotations

import os
import secrets
import sys
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic_ai.mcp import MCPToolset

from mcp_server.tools.admin import APPROVAL_KEY_ENV, approval_signature

from .config import PROJECT_ROOT
from .models import AgentName

WORKING_DB = os.environ.get("CAMPUS_CUSTOMS_DB", str(PROJECT_ROOT / "data" / "campus_customs_new.db"))

# Fresh random key per backend process. It is passed only to this backend's own
# MCP server process and used to sign human approvals. It is never put in any
# agent's prompt or tool list, never logged, and never written to disk.
_APPROVAL_KEY = secrets.token_hex(32)

# Tools no agent may use (operator / backend only).
OPERATOR_TOOLS = frozenset({"reset_working_database", "approve_payment_request", "list_tickets",
                            "mark_ticket_resolved"})

COMMON = {"get_shop_date", "get_ticket", "list_board_posts", "post_ticket_note"}

# Each agent sees only the tools its role needs. This keeps tool definitions
# (and so tokens) per request down, and keeps payment requests with Accounting.
AGENT_TOOLS: dict[AgentName, frozenset[str]] = {
    "boss": frozenset(COMMON | {"list_open_tickets", "update_ticket_status", "list_payment_requests"}),
    "inventory": frozenset(COMMON | {"check_order_fulfillment", "check_stock", "list_vendors",
                                     "check_vendor_dispatch", "create_draft"}),
    "accounting": frozenset(COMMON | {"get_cash_position", "list_invoices", "calculate_margin",
                                      "evaluate_bulk_discount_request", "list_payments", "list_payment_requests",
                                      "request_invoice_payment", "request_rent_payment", "request_purchase_order",
                                      "check_vendor_dispatch", "get_lease_details"}),
    "facilities": frozenset(COMMON | {"check_rent_obligation", "get_lease_details", "create_draft"}),
    "customer_service": frozenset(COMMON | {"create_draft"}),
}
assert not any(OPERATOR_TOOLS & tools for tools in AGENT_TOOLS.values())


def _build_toolset() -> MCPToolset:
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
        env={
            "PYTHONPATH": str(PROJECT_ROOT),
            "CAMPUS_CUSTOMS_DB": str(WORKING_DB),
            APPROVAL_KEY_ENV: _APPROVAL_KEY,
            **({"CAMPUS_CUSTOMS_AUDIT": os.environ["CAMPUS_CUSTOMS_AUDIT"]} if "CAMPUS_CUSTOMS_AUDIT" in os.environ else {}),
        },
        cwd=str(PROJECT_ROOT),
    )
    return MCPToolset(Client(transport), id="campus-customs")


MCP_TOOLSET = _build_toolset()


def toolset_for(agent: AgentName):
    allowed = AGENT_TOOLS[agent]
    return MCP_TOOLSET.filtered(lambda ctx, tool_def: tool_def.name in allowed)


async def call_operator_tool(name: str, args: dict[str, Any] | None = None) -> Any:
    """Call an MCP tool directly (not through an agent): reads for the API, the reset, approvals."""
    async with MCP_TOOLSET:
        return await MCP_TOOLSET.direct_call_tool(name, args or {})


async def approve_as_human(request_id: int, approver: str) -> Any:
    """Sign and send a human approval. Only the FastAPI approve route calls this."""
    approver = approver.strip()
    return await call_operator_tool("approve_payment_request", {
        "request_id": request_id,
        "approver": approver,
        "approval_signature_hex": approval_signature(_APPROVAL_KEY, request_id, approver),
    })
