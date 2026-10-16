"""Tools for price override / discount tickets (ticket 103)."""

from __future__ import annotations

from typing import Any

from ..db import connect, shop_today
from ..queries import (
    get_all_vendors,
    get_inventory_for_sku,
    get_inventory_item,
    get_pricing,
    get_ticket,
    vendor_dispatch_status,
)


def evaluate_bulk_discount_request(ticket_id: int, proposed_unit_price: float | None = None) -> dict[str, Any]:
    """Evaluate a bulk discount request: margin at list price (and at an optional proposed price), stock versus quantity requested, and which vendors could cover any shortfall.

    Reads the ticket, pricing (unit_cost, list_price) for the ticket's SKU,
    inventory for the requested size and all other sizes, and every vendor
    with its lead time and whether unpaid invoices block it from dispatching.
    Read-only; it does not change any price or stock.
    """
    with connect(read_only=True) as conn:
        ticket = get_ticket(conn, ticket_id)
        if ticket is None:
            return {"error": f"ticket {ticket_id} not found"}
        if not ticket["sku"]:
            return {"error": f"ticket {ticket_id} has no sku", "ticket": ticket}

        price = get_pricing(conn, ticket["sku"])
        if price is None:
            return {"error": f"no pricing row for sku {ticket['sku']}", "ticket": ticket}

        today = shop_today(conn)
        qty = ticket["qty"] or 0
        unit_cost = price["unit_cost"]
        list_price = price["list_price"]

        margin: dict[str, Any] = {
            "unit_cost": unit_cost,
            "list_price": list_price,
            "margin_per_unit_at_list": round(list_price - unit_cost, 2),
            "margin_pct_at_list": round((list_price - unit_cost) / list_price * 100, 2) if list_price else None,
            "order_cost_total": round(unit_cost * qty, 2),
            "order_revenue_at_list": round(list_price * qty, 2),
            "break_even_unit_price": unit_cost,
        }
        if proposed_unit_price is not None:
            margin["proposed_unit_price"] = proposed_unit_price
            margin["discount_pct_vs_list"] = round((list_price - proposed_unit_price) / list_price * 100, 2) if list_price else None
            margin["margin_per_unit_at_proposed"] = round(proposed_unit_price - unit_cost, 2)
            margin["order_revenue_at_proposed"] = round(proposed_unit_price * qty, 2)
            margin["order_margin_at_proposed"] = round((proposed_unit_price - unit_cost) * qty, 2)
            margin["proposed_price_above_cost"] = proposed_unit_price > unit_cost

        item = get_inventory_item(conn, ticket["sku"], ticket["size"]) if ticket["size"] else None
        on_hand = item["qty"] if item else 0

        return {
            "shop_date": today.isoformat(),
            "ticket": ticket,
            "requested_qty": qty,
            "pricing": margin,
            "stock_for_requested_size": item,
            "on_hand_qty": on_hand,
            "can_fill_from_stock": on_hand >= qty and qty > 0,
            "shortfall_qty": max(qty - on_hand, 0),
            "other_sizes_in_stock": [
                r for r in get_inventory_for_sku(conn, ticket["sku"]) if r["size"] != ticket["size"]
            ],
            "vendors": [vendor_dispatch_status(conn, v["id"], today) for v in get_all_vendors(conn)],
        }


TOOLS = (evaluate_bulk_discount_request,)
