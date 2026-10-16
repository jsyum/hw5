"""Tools for premises and rent tickets (ticket 102)."""

from __future__ import annotations

from typing import Any

from ..db import connect, shop_today
from ..queries import days_overdue, get_cash_accounts, get_lease, get_ticket


def check_rent_obligation(ticket_id: int) -> dict[str, Any]:
    """Check the lease a rent notice ticket refers to: how much is due, when, and whether cash on hand can cover it.

    Reads the ticket, the lease it links to via tickets.lease_id, desk.date_today
    to compute days until (or past) next_due, and every cash account so the
    rent can be compared against available balances. Read-only; it does not
    record or approve any payment.
    """
    with connect(read_only=True) as conn:
        ticket = get_ticket(conn, ticket_id)
        if ticket is None:
            return {"error": f"ticket {ticket_id} not found"}
        if ticket["lease_id"] is None:
            return {"error": f"ticket {ticket_id} has no lease_id", "ticket": ticket}

        lease = get_lease(conn, ticket["lease_id"])
        if lease is None:
            return {"error": f"lease {ticket['lease_id']} not found", "ticket": ticket}

        today = shop_today(conn)
        overdue_by = days_overdue(lease["next_due"], today)
        accounts = get_cash_accounts(conn)
        for acct in accounts:
            acct["can_cover_rent"] = acct["balance"] >= lease["monthly_rent"]
            acct["balance_after_rent"] = round(acct["balance"] - lease["monthly_rent"], 2)

        return {
            "shop_date": today.isoformat(),
            "ticket": ticket,
            "lease": lease,
            "amount_due": lease["monthly_rent"],
            "next_due": lease["next_due"],
            "days_until_due": -overdue_by,
            "is_overdue": overdue_by > 0,
            "cash_accounts": accounts,
            "total_cash": round(sum(a["balance"] for a in accounts), 2),
        }


def get_lease_details(lease_id: int) -> dict[str, Any]:
    """Return one lease (space, landlord, monthly_rent, next_due) with days until or past next_due versus the shop date."""
    with connect(read_only=True) as conn:
        lease = get_lease(conn, lease_id)
        if lease is None:
            return {"error": f"lease {lease_id} not found"}
        today = shop_today(conn)
        overdue_by = days_overdue(lease["next_due"], today)
        return {"shop_date": today.isoformat(), **lease, "days_until_due": -overdue_by, "is_overdue": overdue_by > 0}


TOOLS = (check_rent_obligation, get_lease_details)
