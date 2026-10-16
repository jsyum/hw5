"""Inventory and vendor tools."""

from __future__ import annotations

from typing import Any

from ..db import connect, shop_today
from ..queries import get_all_vendors, get_inventory_for_sku, get_inventory_item, vendor_dispatch_status


def check_stock(sku: str, size: str | None = None) -> dict[str, Any]:
    """Return on-hand stock for a SKU. With size, returns that size's row; without, every size of the SKU."""
    with connect() as conn:
        if size is not None:
            row = get_inventory_item(conn, sku, size)
            return row if row is not None else {"error": f"no inventory row for sku {sku} size {size}"}
        rows = get_inventory_for_sku(conn, sku)
        return {"sku": sku, "sizes": rows} if rows else {"error": f"no inventory rows for sku {sku}"}


def list_vendors() -> list[dict[str, Any]]:
    """List every vendor with specialty, lead_days, and whether unpaid invoices block it from dispatching (with the blocking invoices)."""
    with connect() as conn:
        today = shop_today(conn)
        return [vendor_dispatch_status(conn, v["id"], today) for v in get_all_vendors(conn)]


def check_vendor_dispatch(vendor_id: int) -> dict[str, Any]:
    """Return one vendor's lead_days and whether any unpaid ('open') invoice blocks it from dispatching, listing each blocking invoice and days overdue."""
    with connect() as conn:
        return vendor_dispatch_status(conn, vendor_id, shop_today(conn))


TOOLS = (check_stock, list_vendors, check_vendor_dispatch)
