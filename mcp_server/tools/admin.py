"""Operator tools. These are NOT given to agents (the backend filters them out).

approve_payment_request only works when the server was started with
CAMPUS_CUSTOMS_APPROVAL_KEY (the FastAPI backend sets a fresh random key for
its own MCP server process) and the call carries an HMAC of the request id and
approver name made with that key. The key never enters any agent's context,
and other MCP clients (such as Claude Code via .mcp.json) do not have it, so
they cannot approve anything.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from .. import audit
from ..db import connect, fetch_one, reset_working_db, utc_now
from ..payments import decide_payment_request

APPROVAL_KEY_ENV = "CAMPUS_CUSTOMS_APPROVAL_KEY"


def approval_signature(key: str, request_id: int, approver: str) -> str:
    return hmac.new(key.encode(), f"{request_id}|{approver.strip()}".encode(), hashlib.sha256).hexdigest()


def reset_working_database() -> dict[str, Any]:
    """OPERATOR ONLY. Restore data/campus_customs_new.db from the original data/campus_customs.db before a full ticket run. Does not touch the audit trail."""
    result = reset_working_db()
    audit.append("database_reset", source="mcp_tool", **result)
    return result


def approve_payment_request(request_id: int, approver: str, approval_signature_hex: str) -> dict[str, Any]:
    """OPERATOR ONLY. Approve and pay a pending payment request on behalf of a named human who clicked Approve in the dashboard. Requires a valid signature from the backend; refuses otherwise."""
    key = os.environ.get(APPROVAL_KEY_ENV, "")
    if not key:
        audit.append("payment_approval_refused", source="mcp_tool", request_id=request_id, approver=approver,
                     reason="approvals are disabled on this server instance")
        return {"approved": False, "reason": "approvals are disabled on this server instance"}
    if not hmac.compare_digest(approval_signature(key, request_id, approver), approval_signature_hex or ""):
        audit.append("payment_approval_refused", source="mcp_tool", request_id=request_id, approver=approver,
                     reason="invalid approval signature")
        return {"approved": False, "reason": "invalid approval signature"}
    try:
        out = decide_payment_request(request_id, "approve", approver, "human_dashboard")
    except (ValueError, PermissionError) as exc:
        return {"approved": False, "reason": str(exc)}
    return {"approved": out["status"] == "paid", **out}


def mark_ticket_resolved(ticket_id: int, run_id: str) -> dict[str, Any]:
    """OPERATOR ONLY. Mark a ticket resolved after its agent run finished, and note the run on the board."""
    with connect(read_only=False) as conn:
        row = fetch_one(conn, "SELECT status FROM tickets WHERE id = ?", (ticket_id,))
        if row is None:
            return {"error": f"ticket {ticket_id} not found"}
        conn.execute("UPDATE tickets SET status = 'resolved' WHERE id = ?", (ticket_id,))
        conn.execute(
            "INSERT INTO board_posts (ticket_id, kind, author_agent, subject, body, created_at) "
            "VALUES (?, 'status_change', 'system', ?, ?, ?)",
            (ticket_id, f"{row['status']} -> resolved", f"Agent run {run_id} finished; ticket marked resolved.", utc_now()),
        )
    out = {"ticket_id": ticket_id, "old_status": row["status"], "new_status": "resolved", "run_id": run_id}
    audit.append("ticket_marked_resolved", source="backend", ticket_id=ticket_id, run_id=run_id,
                 old_status=row["status"])
    return out


TOOLS = (reset_working_database, approve_payment_request, mark_ticket_resolved)
