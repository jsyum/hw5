"""Accounting tools: cash, invoices, margins, payments, and payment REQUESTS.

No tool here (or anywhere in the MCP server) can approve or execute a
payment. Requests stay pending until a human approves them outside the agent
tools (python -m mcp_server.approve).
"""

from __future__ import annotations

from typing import Any

from .. import payments
from ..db import connect, fetch_all, shop_today
from ..queries import days_overdue, get_pricing


def get_cash_position(account: str | None = None) -> list[dict[str, Any]]:
    """Return each cash account's balance, the payment requests still pending against it, and cash available after those pending requests."""
    with connect() as conn:
        names = [account] if account else [r["name"] for r in fetch_all(conn, "SELECT name FROM cash_accounts ORDER BY name")]
        out = []
        for n in names:
            pos = payments.cash_position(conn, n)
            out.append(pos if pos is not None else {"error": f"cash account '{n}' not found"})
        return out


def list_invoices(status: str | None = None, vendor_id: int | None = None) -> list[dict[str, Any]]:
    """List vendor invoices (optionally filtered by status or vendor) with vendor name, days overdue versus the shop date, and any pending payment request."""
    with connect() as conn:
        today = shop_today(conn)
        sql = ("SELECT i.*, v.name AS vendor_name FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE 1=1")
        params: list[Any] = []
        if status:
            sql += " AND i.status = ?"; params.append(status)
        if vendor_id is not None:
            sql += " AND i.vendor_id = ?"; params.append(vendor_id)
        rows = fetch_all(conn, sql + " ORDER BY i.due_date", tuple(params))
        for r in rows:
            r["days_overdue"] = days_overdue(r["due_date"], today)
            r["is_overdue"] = r["status"] == "open" and r["days_overdue"] > 0
            r["pending_payment_requests"] = fetch_all(
                conn, "SELECT id, amount, status FROM payment_requests WHERE kind='invoice' AND ref_id=? "
                      "AND status IN ('pending_approval','approved')", (r["id"],))
        return rows


def calculate_margin(sku: str, unit_price: float, qty: int = 1) -> dict[str, Any]:
    """Compute per-unit and total margin for selling qty of a SKU at unit_price, using pricing.unit_cost and list_price."""
    with connect() as conn:
        p = get_pricing(conn, sku)
        if p is None:
            return {"error": f"no pricing row for sku {sku}"}
        uc, lp = p["unit_cost"], p["list_price"]
        return {
            "sku": sku, "qty": qty, "unit_cost": uc, "list_price": lp, "unit_price": unit_price,
            "discount_pct_vs_list": round((lp - unit_price) / lp * 100, 2) if lp else None,
            "margin_per_unit": round(unit_price - uc, 2),
            "margin_pct": round((unit_price - uc) / unit_price * 100, 2) if unit_price else None,
            "total_revenue": round(unit_price * qty, 2),
            "total_cost": round(uc * qty, 2),
            "total_margin": round((unit_price - uc) * qty, 2),
            "above_cost": unit_price > uc,
        }


def list_payments() -> list[dict[str, Any]]:
    """List completed (human-approved) payments recorded in the payments table."""
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM payments ORDER BY id")


def list_payment_requests(status: str | None = None) -> list[dict[str, Any]]:
    """List payment requests, optionally by status: pending_approval, approved, paid, or rejected."""
    return payments.list_payment_requests(status)


def request_invoice_payment(invoice_id: int, requested_by: str, reason: str,
                            ticket_id: int | None = None, account: str = "checking") -> dict[str, Any]:
    """Create a PENDING request to pay a vendor invoice in full. The amount comes from the invoice. Rejected if the invoice is not open, already has a pending request, or the amount exceeds cash available after other pending requests. A human must approve it; it is not paid by this tool."""
    return payments.request_invoice_payment(invoice_id, requested_by, reason, ticket_id, account)


def request_rent_payment(lease_id: int, requested_by: str, reason: str,
                         ticket_id: int | None = None, account: str = "checking") -> dict[str, Any]:
    """Create a PENDING request to pay a lease's monthly_rent. Rejected if a rent request for that lease is already pending or the amount exceeds cash available after other pending requests. A human must approve it; it is not paid by this tool."""
    return payments.request_rent_payment(lease_id, requested_by, reason, ticket_id, account)


def request_purchase_order(vendor_id: int, sku: str, size: str, qty: int, requested_by: str, reason: str,
                           ticket_id: int | None = None, account: str = "checking") -> dict[str, Any]:
    """Create a PENDING purchase order (restock) request. Cost = pricing.unit_cost x qty; expected arrival = shop date + vendor lead_days. Rejected if the vendor has unpaid invoices without a pending payment request, or the cost exceeds cash available after other pending requests. A human must approve it; it is not paid by this tool."""
    return payments.request_purchase_order(vendor_id, sku, size, qty, requested_by, reason, ticket_id, account)


TOOLS = (get_cash_position, list_invoices, calculate_margin, list_payments, list_payment_requests,
         request_invoice_payment, request_rent_payment, request_purchase_order)
