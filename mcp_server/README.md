# Campus Customs MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes the Campus Customs shop database to the agent team as MCP tools. Every agent (Boss, Inventory, Accounting, Facilities, Customer Service) will call tools from this server; nothing is wired to agents or the backend yet.

## Database

The server reads **only** the working copy at `data/campus_customs_new.db` (path resolved in `db.py`). The optional `CAMPUS_CUSTOMS_DB` environment variable overrides the path; the project `.mcp.json` sets it explicitly to the working copy. The original `data/campus_customs.db` is never opened. All current tools open the database in read-only mode.

**Update (Problem 5):** The original is now opened read-only for one purpose only: `reset_working_database` copies it over the working copy. Write tools now exist, and they write only to the working copy. The server also adds two board tables to the working copy, `payment_requests` and `board_posts`, along with guard triggers. These are recreated after every reset.

## Tools

| Tool | Ticket | What it does |
|---|---|---|
| `check_order_fulfillment(ticket_id)` | 101 | Stock for the ordered SKU and size, other sizes on hand, and the linked invoice with its vendor's lead time and dispatch-block status. |
| `check_rent_obligation(ticket_id)` | 102 | The lease behind a rent notice: amount, due date, days until due, and whether each cash account can cover it. |
| `evaluate_bulk_discount_request(ticket_id, proposed_unit_price=None)` | 103 | Margin at list price (and at a proposed price), stock versus quantity requested, shortfall, and every vendor's lead time and dispatch-block status. |
| `get_lease_details(lease_id)` | 102 | One lease with days until or past `next_due`. |
| `get_shop_date()` | all | `desk.date_today` and desk notes. |
| `get_ticket(ticket_id)` | all | One ticket row. |
| `list_open_tickets()` | all | Tickets not yet resolved. |
| `check_stock(sku, size=None)` | 101, 103 | Stock for one size or every size of a SKU. |
| `list_vendors()` | 101, 103 | Every vendor with lead time and dispatch-block status. |
| `check_vendor_dispatch(vendor_id)` | 101, 103 | One vendor's lead time and blocking invoices. |
| `get_cash_position(account=None)` | all | Balance, pending payment requests, and cash left after them. |
| `list_invoices(status=None, vendor_id=None)` | 101, 103 | Invoices with days overdue and any pending payment request. |
| `calculate_margin(sku, unit_price, qty=1)` | 103 | Per-unit and total margin at a given price. |
| `list_payments()` | all | Completed, human-approved payments. |
| `list_payment_requests(status=None)` | all | Payment requests by status. |
| `request_invoice_payment(invoice_id, requested_by, reason, ticket_id=None, account="checking")` | 101, 103 | Creates a **pending** request to pay an open invoice. Does not pay. |
| `request_rent_payment(lease_id, requested_by, reason, ticket_id=None, account="checking")` | 102 | Creates a **pending** rent request. Does not pay. |
| `request_purchase_order(vendor_id, sku, size, qty, requested_by, reason, ticket_id=None, account="checking")` | 101, 103 | Creates a **pending** restock order. It is refused while the vendor is blocked by an unpaid invoice that has no pending request. Does not pay. |
| `create_draft(ticket_id, author_agent, recipient, recipient_type, subject, body)` | all | Saves a message as a draft on the board. Never sends it. |
| `post_ticket_note(ticket_id, author_agent, note)` | all | Internal note on a ticket. |
| `update_ticket_status(ticket_id, status, author_agent, note)` | all | Sets `open`, `in_progress`, `blocked`, `awaiting_approval`, or `resolved` and records why. |
| `list_board_posts(ticket_id)` | all | Drafts, notes, and status changes for a ticket. |
| `reset_working_database()` | operator | Restores the working copy from the original. Hidden from agents. |
| `list_tickets()` | operator | Every ticket with its status, for the backend's ticket list. Hidden from agents. |
| `approve_payment_request(request_id, approver, approval_signature_hex)` | operator | Pays a pending request for a named human who clicked Approve in the dashboard. Works only with a signature from the backend's per-process secret key. Hidden from agents, and refused for any client without that key. |
| `mark_ticket_resolved(ticket_id, run_id)` | operator | Marks a ticket resolved after its agent run finishes and notes the run on the board. Hidden from agents. |

All tools treat `desk.date_today` as the current date and return it as `shop_date`.

## Layout

```
mcp_server/
  server.py       FastMCP app; registers all tools
  db.py           Working-database path and connection helpers
  queries.py      Shared read queries (ticket, inventory, vendor status, ...)
  tools/
    __init__.py   TOOL_MODULES registry and register_all()
    orders.py     Customer order tools
    facilities.py Lease and rent tools
    pricing.py    Discount and margin tools
    shop.py       Shop date and ticket tools
    inventory.py  Stock and vendor tools
    accounting.py Cash, invoice, margin, payment-request tools
    board.py      Draft, note, and status tools
    admin.py      Operator-only reset tool
  payments.py     Payment request rules and the human-only approval logic
  approve.py      Interactive human approval CLI (not an MCP tool)
  audit.py        Append-only writer for output/audit_trail.json
```

To add a tool later: write a plain function in the relevant `tools/` module (or a new module), add it to that module's `TOOLS` tuple, and, for a new module, add it to `TOOL_MODULES` in `tools/__init__.py`.

## Running

Dependencies are in the project-root `requirements.txt` (`fastmcp`). From the project root:

```
python -m mcp_server.server
```

Claude Code launches it automatically from the project-root `.mcp.json` (server name `campus-customs`), using the `.venv` interpreter with `PYTHONPATH` and `CAMPUS_CUSTOMS_DB` set.

## Model provider note

The MCP server itself makes no model calls. The agent team that uses these tools (`backend/`) calls `gpt-6-luna` directly through the OpenAI API, authenticated with `OPENAI_API_KEY` from `.env`, instead of through Portkey. This change was made per Professor Zaman because of Portkey account access issues. The model is still `gpt-6-luna` only, and the key is never hard-coded, logged, or printed.

## Payment approval (human only)

No MCP tool can approve or execute a payment. Agents can only create requests, which stay `pending_approval` and are not recorded as paid. A human approves them from a terminal:

```
python -m mcp_server.approve --list   # show pending requests
python -m mcp_server.approve          # approve, reject, or skip each one
```

The approval program refuses to run without an interactive terminal. It needs the approver's name, which cannot be an agent name, and a typed `yes` for each payment. On approval it re-checks the live balance, and for invoices that the invoice is still open. It then records the row in `payments`, deducts the cash, and marks the invoice paid or advances the lease due date. Database triggers independently refuse any payment without a matching human-approved request, and any cash balance below zero. Every request, approval, rejection, and reset is appended to `output/audit_trail.json`.

**Update (Problem 7):** The FastAPI backend's approve route is a second human approval path, next to the terminal program. When the backend starts, it creates a random key that it passes only to its own MCP server process, in `CAMPUS_CUSTOMS_APPROVAL_KEY`. It signs each human approval with that key. `approve_payment_request` refuses any call without a valid signature. MCP clients that never receive the key, such as Claude Code through `.mcp.json`, therefore cannot approve anything. Approvals record `decision_source = 'human_dashboard'`.
