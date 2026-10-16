"""Tools for customer order tickets (ticket 101)."""

from __future__ import annotations

from typing import Any

from ..db import connect, shop_today
from ..queries import (
    days_overdue,
    get_inventory_for_sku,
    get_inventory_item,
    get_invoice,
    get_ticket,
    vendor_dispatch_status,
)


def check_order_fulfillment(ticket_id: int) -> dict[str, Any]:
    """Check whether a customer order ticket can be filled from stock, and if not, whether the vendor restock it depends on is blocked.

    Reads the ticket, the inventory row for the ticket's SKU and size (plus all
    other sizes of that SKU), and the invoice the ticket links to via
    tickets.invoice_id, including that invoice's vendor, lead time, and whether
    unpaid invoices block the vendor from dispatching. Dates are judged against
    desk.date_today. Read-only.
    """
    with connect(read_only=True) as conn:
        ticket = get_ticket(conn, ticket_id)
        if ticket is None:
            return {"error": f"ticket {ticket_id} not found"}
        if not ticket["sku"] or not ticket["size"]:
            return {"error": f"ticket {ticket_id} has no sku/size to check", "ticket": ticket}

        today = shop_today(conn)
        item = get_inventory_item(conn, ticket["sku"], ticket["size"])
        requested = ticket["qty"] or 0
        on_hand = item["qty"] if item else 0

        result: dict[str, Any] = {
            "shop_date": today.isoformat(),
            "ticket": ticket,
            "requested_qty": requested,
            "stock_for_requested_size": item,
            "on_hand_qty": on_hand,
            "can_fill_from_stock": on_hand >= requested and requested > 0,
            "shortfall_qty": max(requested - on_hand, 0),
            "other_sizes_in_stock": [
                r for r in get_inventory_for_sku(conn, ticket["sku"]) if r["size"] != ticket["size"]
            ],
            "linked_invoice": None,
        }

        if ticket["invoice_id"] is not None:
            invoice = get_invoice(conn, ticket["invoice_id"])
            if invoice is not None:
                invoice["days_overdue"] = days_overdue(invoice["due_date"], today)
                invoice["vendor"] = vendor_dispatch_status(conn, invoice["vendor_id"], today)
            result["linked_invoice"] = invoice

        return result


TOOLS = (check_order_fulfillment,)
