"""Reusable read queries shared by more than one tool.

Everything here reflects the real schema of campus_customs.db. Column names
and relationships are exactly those found by inspection (see output/harness.md).
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any

from .db import fetch_all, fetch_one

# The only invoice status present in the source data is "open". An "open"
# invoice is unpaid and therefore blocks its vendor from dispatching.
UNPAID_INVOICE_STATUS = "open"


def get_ticket(conn: sqlite3.Connection, ticket_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))


def get_inventory_item(conn: sqlite3.Connection, sku: str, size: str) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size))


def get_inventory_for_sku(conn: sqlite3.Connection, sku: str) -> list[dict[str, Any]]:
    return fetch_all(conn, "SELECT * FROM inventory WHERE sku = ? ORDER BY size", (sku,))


def get_pricing(conn: sqlite3.Connection, sku: str) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM pricing WHERE sku = ?", (sku,))


def get_vendor(conn: sqlite3.Connection, vendor_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM vendors WHERE id = ?", (vendor_id,))


def get_all_vendors(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return fetch_all(conn, "SELECT * FROM vendors ORDER BY id")


def get_lease(conn: sqlite3.Connection, lease_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM leases WHERE id = ?", (lease_id,))


def get_invoice(conn: sqlite3.Connection, invoice_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM invoices WHERE id = ?", (invoice_id,))


def get_cash_accounts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return fetch_all(conn, "SELECT * FROM cash_accounts ORDER BY name")


def unpaid_invoices_for_vendor(conn: sqlite3.Connection, vendor_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT * FROM invoices WHERE vendor_id = ? AND status = ? ORDER BY due_date",
        (vendor_id, UNPAID_INVOICE_STATUS),
    )


def vendor_dispatch_status(conn: sqlite3.Connection, vendor_id: int, today: date) -> dict[str, Any]:
    """A vendor plus whether unpaid invoices block it from dispatching."""
    vendor = get_vendor(conn, vendor_id)
    if vendor is None:
        return {"vendor_id": vendor_id, "error": "vendor not found"}
    unpaid = unpaid_invoices_for_vendor(conn, vendor_id)
    for inv in unpaid:
        inv["days_overdue"] = days_overdue(inv["due_date"], today)
    return {
        **vendor,
        "blocked_from_dispatch": len(unpaid) > 0,
        "unpaid_invoices": unpaid,
    }


def days_overdue(due_date_iso: str, today: date) -> int:
    """Positive when past due, zero or negative when not yet due."""
    return (today - date.fromisoformat(due_date_iso)).days
