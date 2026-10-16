"""Payment requests and human approval.

Agents can only CREATE payment requests (via MCP tools in tools/accounting.py).
A request stays 'pending_approval' and nothing is paid until a human approves
it through decide_payment_request(), which is NOT registered as an MCP tool.
The only caller is the interactive approval CLI (mcp_server/approve.py).
Database triggers (see db.py) independently refuse any payment row that lacks
a human-approved request and any balance that would drop below zero.
"""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date, timedelta
from typing import Any, Literal

from . import audit
from .db import HUMAN_DECISION_SOURCES, connect, fetch_all, fetch_one, shop_today, utc_now
from .queries import UNPAID_INVOICE_STATUS, days_overdue

AGENT_NAMES = ("boss", "inventory", "accounting", "facilities", "customer_service")
PAID_INVOICE_STATUS = "paid"


# ---------------------------------------------------------------- helpers

def add_one_month(d: date) -> date:
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def cash_position(conn: sqlite3.Connection, account: str) -> dict[str, Any] | None:
    acct = fetch_one(conn, "SELECT * FROM cash_accounts WHERE name = ?", (account,))
    if acct is None:
        return None
    pending = fetch_all(
        conn,
        "SELECT id, kind, ref_id, amount, requested_by, reason, ticket_id FROM payment_requests "
        "WHERE account = ? AND status IN ('pending_approval', 'approved') ORDER BY id",
        (account,),
    )
    pending_total = round(sum(p["amount"] for p in pending), 2)
    return {
        **acct,
        "pending_requests": pending,
        "pending_total": pending_total,
        "available_after_pending": round(acct["balance"] - pending_total, 2),
    }


def _reject(reason: str, **extra: Any) -> dict[str, Any]:
    return {"accepted": False, "status": "rejected", "reason": reason, **extra}


def _create_request(conn: sqlite3.Connection, *, kind: str, ref_id: int | None, amount: float,
                    account: str, requested_by: str, reason: str, ticket_id: int | None,
                    vendor_id: int | None = None, sku: str | None = None, size: str | None = None,
                    qty: int | None = None, expected_arrival: str | None = None) -> dict[str, Any]:
    if requested_by not in AGENT_NAMES:
        return _reject(f"requested_by must be one of {list(AGENT_NAMES)}")
    if ticket_id is not None and fetch_one(conn, "SELECT id FROM tickets WHERE id = ?", (ticket_id,)) is None:
        return _reject(f"ticket {ticket_id} not found")
    pos = cash_position(conn, account)
    if pos is None:
        return _reject(f"cash account '{account}' not found")
    amount = round(float(amount), 2)
    if amount <= 0:
        return _reject("amount must be positive")
    if amount > pos["balance"]:
        return _reject(f"amount {amount:.2f} exceeds the {account} balance of {pos['balance']:.2f}",
                       cash_position=pos)
    if amount > pos["available_after_pending"]:
        return _reject(
            f"amount {amount:.2f} exceeds cash available after other pending requests "
            f"({pos['balance']:.2f} balance - {pos['pending_total']:.2f} pending = {pos['available_after_pending']:.2f})",
            cash_position=pos,
        )
    cur = conn.execute(
        "INSERT INTO payment_requests (kind, ref_id, ticket_id, vendor_id, sku, size, qty, amount, account, "
        "requested_by, reason, status, expected_arrival, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_approval', ?, ?)",
        (kind, ref_id, ticket_id, vendor_id, sku, size, qty, amount, account, requested_by, reason,
         expected_arrival, utc_now()),
    )
    req = fetch_one(conn, "SELECT * FROM payment_requests WHERE id = ?", (cur.lastrowid,))
    audit.append("payment_requested", source="mcp_tool", request=req)
    return {
        "accepted": True,
        "status": "pending_approval",
        "request": req,
        "message": "Payment request created and PENDING HUMAN APPROVAL. It is not paid and has not been recorded "
                   "as a payment. Only a human can approve it, outside the agent tools.",
        "cash_after_this_request_if_approved": round(pos["available_after_pending"] - amount, 2),
    }


# ---------------------------------------------------------- agent-facing (via MCP tools)

def request_invoice_payment(invoice_id: int, requested_by: str, reason: str,
                            ticket_id: int | None = None, account: str = "checking") -> dict[str, Any]:
    with connect(read_only=False) as conn:
        inv = fetch_one(conn, "SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        if inv is None:
            return _reject(f"invoice {invoice_id} not found")
        if inv["status"] != UNPAID_INVOICE_STATUS:
            return _reject(f"invoice {invoice_id} has status '{inv['status']}', not '{UNPAID_INVOICE_STATUS}'")
        dup = fetch_one(conn, "SELECT id FROM payment_requests WHERE kind='invoice' AND ref_id=? "
                              "AND status IN ('pending_approval','approved')", (invoice_id,))
        if dup:
            return _reject(f"invoice {invoice_id} already has payment request {dup['id']} pending")
        return _create_request(conn, kind="invoice", ref_id=invoice_id, amount=inv["amount"], account=account,
                               requested_by=requested_by, reason=reason, ticket_id=ticket_id,
                               vendor_id=inv["vendor_id"])


def request_rent_payment(lease_id: int, requested_by: str, reason: str,
                         ticket_id: int | None = None, account: str = "checking") -> dict[str, Any]:
    with connect(read_only=False) as conn:
        lease = fetch_one(conn, "SELECT * FROM leases WHERE id = ?", (lease_id,))
        if lease is None:
            return _reject(f"lease {lease_id} not found")
        dup = fetch_one(conn, "SELECT id FROM payment_requests WHERE kind='rent' AND ref_id=? "
                              "AND status IN ('pending_approval','approved')", (lease_id,))
        if dup:
            return _reject(f"lease {lease_id} already has rent payment request {dup['id']} pending")
        return _create_request(conn, kind="rent", ref_id=lease_id, amount=lease["monthly_rent"], account=account,
                               requested_by=requested_by,
                               reason=f"{reason} (rent for {lease['space_name']}, due {lease['next_due']})",
                               ticket_id=ticket_id)


def request_purchase_order(vendor_id: int, sku: str, size: str, qty: int, requested_by: str, reason: str,
                           ticket_id: int | None = None, account: str = "checking") -> dict[str, Any]:
    with connect(read_only=False) as conn:
        vendor = fetch_one(conn, "SELECT * FROM vendors WHERE id = ?", (vendor_id,))
        if vendor is None:
            return _reject(f"vendor {vendor_id} not found")
        if qty is None or qty <= 0:
            return _reject("qty must be a positive integer")
        if fetch_one(conn, "SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)) is None:
            return _reject(f"no inventory row for sku {sku} size {size}")
        price = fetch_one(conn, "SELECT * FROM pricing WHERE sku = ?", (sku,))
        if price is None:
            return _reject(f"no pricing row for sku {sku}; cannot compute purchase cost")
        today = shop_today(conn)
        unpaid = fetch_all(conn, "SELECT * FROM invoices WHERE vendor_id = ? AND status = ?",
                           (vendor_id, UNPAID_INVOICE_STATUS))
        uncovered = [i for i in unpaid if not fetch_one(
            conn, "SELECT id FROM payment_requests WHERE kind='invoice' AND ref_id=? "
                  "AND status IN ('pending_approval','approved')", (i["id"],))]
        if uncovered:
            return _reject(
                f"vendor {vendor_id} ({vendor['name']}) is blocked from dispatching by unpaid invoice(s) "
                f"{[i['id'] for i in uncovered]}; request payment of those first",
                blocking_invoices=uncovered,
            )
        result = _create_request(
            conn, kind="purchase_order", ref_id=vendor_id, amount=price["unit_cost"] * qty, account=account,
            requested_by=requested_by,
            reason=f"{reason} ({qty} x {sku} {size} at unit_cost {price['unit_cost']:.2f} from {vendor['name']})",
            ticket_id=ticket_id, vendor_id=vendor_id, sku=sku, size=size, qty=qty,
            expected_arrival=(today + timedelta(days=vendor["lead_days"])).isoformat(),
        )
        if result.get("accepted") and unpaid:
            result["note"] = (f"Vendor is still blocked by invoice(s) {[i['id'] for i in unpaid]}; this order "
                              "cannot be approved until those are paid.")
        return result


def list_payment_requests(status: str | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if status:
            return fetch_all(conn, "SELECT * FROM payment_requests WHERE status = ? ORDER BY id", (status,))
        return fetch_all(conn, "SELECT * FROM payment_requests ORDER BY id")


# --------------------------------------------------- HUMAN ONLY (never an MCP tool)

def decide_payment_request(request_id: int, decision: Literal["approve", "reject"], decided_by: str,
                           decision_source: str, note: str | None = None) -> dict[str, Any]:
    """Approve-and-pay or reject a pending request. Called only from the human approval CLI."""
    if decision_source not in HUMAN_DECISION_SOURCES:
        raise PermissionError(f"decision_source must be one of {HUMAN_DECISION_SOURCES}")
    decided_by = (decided_by or "").strip()
    if not decided_by or decided_by.lower() in AGENT_NAMES:
        raise PermissionError("a human approver name is required (agent names are not accepted)")

    with connect(read_only=False) as conn:
        req = fetch_one(conn, "SELECT * FROM payment_requests WHERE id = ?", (request_id,))
        if req is None:
            raise ValueError(f"payment request {request_id} not found")
        if req["status"] != "pending_approval":
            raise ValueError(f"payment request {request_id} is '{req['status']}', not pending_approval")
        today = shop_today(conn)

        def finish_reject(reason: str) -> dict[str, Any]:
            conn.execute("UPDATE payment_requests SET status='rejected', decided_by=?, decision_source=?, "
                         "decision_note=?, decided_at=? WHERE id=?",
                         (decided_by, decision_source, reason, utc_now(), request_id))
            out = {"request_id": request_id, "status": "rejected", "reason": reason}
            audit.append("payment_rejected", source=decision_source, decided_by=decided_by, **out)
            return out

        if decision == "reject":
            return finish_reject(note or "rejected by human approver")

        # Re-validate against current data at approval time.
        acct = fetch_one(conn, "SELECT * FROM cash_accounts WHERE name = ?", (req["account"],))
        if acct is None:
            return finish_reject(f"cash account '{req['account']}' no longer exists")
        if req["amount"] > acct["balance"]:
            return finish_reject(f"amount {req['amount']:.2f} exceeds current {acct['name']} balance {acct['balance']:.2f}")
        if req["kind"] == "invoice":
            inv = fetch_one(conn, "SELECT * FROM invoices WHERE id = ?", (req["ref_id"],))
            if inv is None or inv["status"] != UNPAID_INVOICE_STATUS:
                return finish_reject(f"invoice {req['ref_id']} is no longer unpaid")
        if req["kind"] == "purchase_order":
            blocking = fetch_all(conn, "SELECT id FROM invoices WHERE vendor_id = ? AND status = ?",
                                 (req["vendor_id"], UNPAID_INVOICE_STATUS))
            if blocking:
                raise ValueError(f"vendor {req['vendor_id']} is still blocked by unpaid invoice(s) "
                                 f"{[b['id'] for b in blocking]}; approve those payments first. Request left pending.")

        conn.execute("UPDATE payment_requests SET status='approved', decided_by=?, decision_source=?, "
                     "decision_note=?, decided_at=? WHERE id=?",
                     (decided_by, decision_source, note, utc_now(), request_id))
        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
            (req["kind"], req["ref_id"], req["amount"], req["account"], today.isoformat(), decided_by),
        )
        payment_id = cur.lastrowid
        conn.execute("UPDATE cash_accounts SET balance = round(balance - ?, 2), date = ? WHERE name = ?",
                     (req["amount"], today.isoformat(), req["account"]))
        side_effect = None
        if req["kind"] == "invoice":
            conn.execute("UPDATE invoices SET status = ? WHERE id = ?", (PAID_INVOICE_STATUS, req["ref_id"]))
            side_effect = f"invoice {req['ref_id']} marked '{PAID_INVOICE_STATUS}'"
        elif req["kind"] == "rent":
            lease = fetch_one(conn, "SELECT next_due FROM leases WHERE id = ?", (req["ref_id"],))
            new_due = add_one_month(date.fromisoformat(lease["next_due"])).isoformat()
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (new_due, req["ref_id"]))
            side_effect = f"lease {req['ref_id']} next_due advanced from {lease['next_due']} to {new_due}"
        conn.execute("UPDATE payment_requests SET status='paid', payment_id=? WHERE id=?", (payment_id, request_id))
        payment = fetch_one(conn, "SELECT * FROM payments WHERE id = ?", (payment_id,))
        balance = fetch_one(conn, "SELECT balance FROM cash_accounts WHERE name = ?", (req["account"],))["balance"]

    out = {"request_id": request_id, "status": "paid", "payment": payment,
           "new_balance": balance, "side_effect": side_effect}
    audit.append("payment_approved_and_recorded", source=decision_source, decided_by=decided_by, **out)
    return out
