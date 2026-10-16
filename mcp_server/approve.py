"""Interactive HUMAN payment approval.

    python -m mcp_server.approve           # review each pending request
    python -m mcp_server.approve --list    # just list pending requests

This is the only way a payment request gets approved and paid. It is not an
MCP tool, so no agent can call it. It refuses to run without an interactive
terminal, and each approval needs a typed "yes" plus the approver's name.
"""

from __future__ import annotations

import sys

from .payments import decide_payment_request, list_payment_requests

SOURCE = "human_cli"


def _show(req: dict) -> None:
    print(f"\nRequest #{req['id']}  [{req['kind']}]  amount {req['amount']:.2f} from '{req['account']}'")
    print(f"  ticket: {req['ticket_id']}  ref_id: {req['ref_id']}  vendor_id: {req['vendor_id']}")
    if req["sku"]:
        print(f"  item: {req['qty']} x {req['sku']} {req['size']}  expected arrival: {req['expected_arrival']}")
    print(f"  requested by agent: {req['requested_by']}")
    print(f"  reason: {req['reason']}")


def main() -> int:
    pending = list_payment_requests("pending_approval")
    if "--list" in sys.argv:
        for r in pending:
            _show(r)
        print(f"\n{len(pending)} pending request(s).")
        return 0
    if not sys.stdin.isatty():
        print("Refusing to run: payment approval requires an interactive human at a terminal.", file=sys.stderr)
        return 2
    if not pending:
        print("No payment requests are pending approval.")
        return 0

    approver = input("Your name (human approver): ").strip()
    if not approver:
        print("An approver name is required.", file=sys.stderr)
        return 2

    for req in pending:
        _show(req)
        answer = input("Approve and pay this request? Type 'yes', 'no' (reject), or press Enter to skip: ").strip().lower()
        try:
            if answer == "yes":
                out = decide_payment_request(req["id"], "approve", approver, SOURCE)
                print(f"  PAID. payment id {out['payment']['id']}, new balance {out['new_balance']:.2f}. {out['side_effect'] or ''}")
            elif answer == "no":
                note = input("  Reason for rejection (optional): ").strip() or None
                out = decide_payment_request(req["id"], "reject", approver, SOURCE, note)
                print(f"  REJECTED. {out['reason']}")
            else:
                print("  Skipped; request stays pending and nothing is paid.")
        except (ValueError, PermissionError) as exc:
            print(f"  NOT PAID: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
