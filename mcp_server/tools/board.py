"""Ticket board tools: drafts, notes, and status. Nothing here sends anything."""

from __future__ import annotations

from typing import Any

from ..db import connect, fetch_all, fetch_one, utc_now
from ..payments import AGENT_NAMES

TICKET_STATUSES = ("open", "in_progress", "blocked", "awaiting_approval", "resolved")
RECIPIENT_TYPES = ("customer", "vendor", "landlord", "other")


def _check(conn, ticket_id: int, author_agent: str) -> str | None:
    if author_agent not in AGENT_NAMES:
        return f"author_agent must be one of {list(AGENT_NAMES)}"
    if fetch_one(conn, "SELECT id FROM tickets WHERE id = ?", (ticket_id,)) is None:
        return f"ticket {ticket_id} not found"
    return None


def _post(conn, **f: Any) -> dict[str, Any]:
    cur = conn.execute(
        "INSERT INTO board_posts (ticket_id, kind, author_agent, recipient, recipient_type, subject, body, status, created_at) "
        "VALUES (:ticket_id, :kind, :author_agent, :recipient, :recipient_type, :subject, :body, :status, :created_at)",
        {"recipient": None, "recipient_type": None, "subject": None, "status": None, "created_at": utc_now(), **f},
    )
    return fetch_one(conn, "SELECT * FROM board_posts WHERE id = ?", (cur.lastrowid,))


def create_draft(ticket_id: int, author_agent: str, recipient: str, recipient_type: str,
                 subject: str, body: str) -> dict[str, Any]:
    """Save a message to a customer, vendor, or landlord as a DRAFT on the ticket board. Drafts are never sent; a human reviews them."""
    if recipient_type not in RECIPIENT_TYPES:
        return {"error": f"recipient_type must be one of {list(RECIPIENT_TYPES)}"}
    with connect(read_only=False) as conn:
        if err := _check(conn, ticket_id, author_agent):
            return {"error": err}
        post = _post(conn, ticket_id=ticket_id, kind="draft", author_agent=author_agent, recipient=recipient,
                     recipient_type=recipient_type, subject=subject, body=body, status="draft")
        return {"saved": True, "sent": False, "draft": post, "message": "Saved as a draft on the board. Nothing was sent."}


def post_ticket_note(ticket_id: int, author_agent: str, note: str) -> dict[str, Any]:
    """Add an internal note (findings, blockers, recommendations) to a ticket on the board."""
    with connect(read_only=False) as conn:
        if err := _check(conn, ticket_id, author_agent):
            return {"error": err}
        return {"saved": True, "post": _post(conn, ticket_id=ticket_id, kind="note", author_agent=author_agent, body=note)}


def update_ticket_status(ticket_id: int, status: str, author_agent: str, note: str) -> dict[str, Any]:
    """Change a ticket's status (open, in_progress, blocked, awaiting_approval, resolved) and record why on the board."""
    if status not in TICKET_STATUSES:
        return {"error": f"status must be one of {list(TICKET_STATUSES)}"}
    with connect(read_only=False) as conn:
        if err := _check(conn, ticket_id, author_agent):
            return {"error": err}
        old = fetch_one(conn, "SELECT status FROM tickets WHERE id = ?", (ticket_id,))["status"]
        conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        post = _post(conn, ticket_id=ticket_id, kind="status_change", author_agent=author_agent,
                     subject=f"{old} -> {status}", body=note)
        return {"updated": True, "ticket_id": ticket_id, "old_status": old, "new_status": status, "post": post}


def list_board_posts(ticket_id: int) -> list[dict[str, Any]]:
    """List every draft, note, and status change posted on a ticket, oldest first."""
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM board_posts WHERE ticket_id = ? ORDER BY id", (ticket_id,))


TOOLS = (create_draft, post_ticket_note, update_ticket_status, list_board_posts)
