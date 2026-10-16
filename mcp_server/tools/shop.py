"""General shop tools: current shop date and the ticket board."""

from __future__ import annotations

from typing import Any

from ..db import connect, fetch_all, fetch_one, shop_today


def get_shop_date() -> dict[str, Any]:
    """Return the shop's current date (desk.date_today) and desk notes. Use this date, never the real clock, for due/overdue checks."""
    with connect() as conn:
        desk = fetch_one(conn, "SELECT * FROM desk LIMIT 1")
        return {"shop_date": shop_today(conn).isoformat(), "desk": desk}


def get_ticket(ticket_id: int) -> dict[str, Any]:
    """Return one ticket row (type, requester, subject, sku, size, qty, lease_id, invoice_id, status, notes, created_at)."""
    with connect() as conn:
        t = fetch_one(conn, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return t if t is not None else {"error": f"ticket {ticket_id} not found"}


def list_open_tickets() -> list[dict[str, Any]]:
    """List every ticket whose status is not 'resolved', oldest first."""
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM tickets WHERE status <> 'resolved' ORDER BY created_at, id")


def list_tickets() -> list[dict[str, Any]]:
    """List every ticket on the board with its current status, including resolved ones."""
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM tickets ORDER BY id")


TOOLS = (get_shop_date, get_ticket, list_open_tickets, list_tickets)
