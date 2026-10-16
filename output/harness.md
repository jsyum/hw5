# Campus Customs Harness

Reference document for the agent team. Built from direct inspection of `data/campus_customs.db` (SQLite). Nothing here is assumed beyond what the schema and rows contain.

## Contents

| Topic | Section |
|---|---|
| Tables and relationships | Tables, Relationships, and Board tables added to the working copy (under Problem 5) |
| MCP tools | MCP tools (26), under Problem 5 |
| The five agents | Agents, under Problem 5 |
| API routes | Problem 7: Backend Routes |
| Dashboard | Problem 8: Dashboard |
| Safety rules and limits | Safety, and Loop and token limits, under Problem 5 |
| What happened when the tickets ran | Problem 9: Results |

## Databases

| File | Role |
|---|---|
| `data/campus_customs.db` | Original source. Never modified. |
| `data/campus_customs_new.db` | Working copy. All tools read and write here, only through the MCP server. Restored from the original before each full ticket run. It also holds the board tables `payment_requests` and `board_posts`. |

Shop's current date: `desk.date_today = 2026-08-31`.

## Tables

### desk
Fields: `date_today` (TEXT, not null), `notes` (TEXT).
Holds the shop's current date, which every agent must use instead of the real clock when judging what is due or overdue.

### tickets
Fields: `id` (INTEGER PK), `type` (TEXT, not null), `requester` (TEXT, not null), `subject` (TEXT, not null), `sku` (TEXT), `size` (TEXT), `qty` (INTEGER), `lease_id` (INTEGER, FK → leases.id), `invoice_id` (INTEGER, FK → invoices.id), `status` (TEXT, not null), `notes` (TEXT), `created_at` (TEXT, not null).
The shared board itself: every unit of work the Boss assigns starts as a ticket row, and its optional columns point at the inventory, lease, or invoice the ticket is about.

### inventory
Fields: `sku` (TEXT, not null), `name` (TEXT, not null), `size` (TEXT, not null), `qty` (INTEGER, not null), `location` (TEXT, not null). Composite PK (`sku`, `size`).
Stock on hand per SKU and size, which the Inventory agent checks to confirm an order can be filled or to spot a shortfall.

### pricing
Fields: `sku` (TEXT PK), `unit_cost` (REAL, not null), `list_price` (REAL, not null).
One cost and list price per SKU, which Accounting uses to compute margins when a discount is requested.

### vendors
Fields: `id` (INTEGER PK), `name` (TEXT, not null), `specialty` (TEXT, not null), `lead_days` (INTEGER, not null).
The suppliers who can restock, with the lead time that determines how long a reorder takes to arrive.

### leases
Fields: `id` (INTEGER PK), `space_name` (TEXT, not null), `landlord` (TEXT, not null), `monthly_rent` (REAL, not null), `next_due` (TEXT, not null), `notes` (TEXT).
The premises obligations Facilities watches, including how much rent is owed and when.

### cash_accounts
Fields: `name` (TEXT PK), `balance` (REAL, not null), `date` (TEXT, not null).
Available funds, which cap every payment because a balance may never drop below zero.

### payments
Fields: `id` (INTEGER PK), `kind` (TEXT, not null), `ref_id` (INTEGER), `amount` (REAL, not null), `account` (TEXT, not null), `paid_at` (TEXT, not null), `approved_by` (TEXT, not null).
The record of completed, human-approved cash outflows; it is empty in the source data. The schema declares no foreign key on `ref_id` and no fixed vocabulary for `kind`.

### invoices
Fields: `id` (INTEGER PK), `vendor_id` (INTEGER, not null, FK → vendors.id), `amount` (REAL, not null), `due_date` (TEXT, not null), `status` (TEXT, not null), `description` (TEXT).
Bills owed to vendors; an unpaid one blocks that vendor from dispatching anything else, so Accounting must clear it before Inventory can restock from them.

## Relationships

Declared foreign keys:

- `tickets.lease_id` → `leases.id`
- `tickets.invoice_id` → `invoices.id`
- `invoices.vendor_id` → `vendors.id`

Links by shared value (no declared constraint):

- `tickets.sku` + `tickets.size` match `inventory.sku` + `inventory.size`
- `inventory.sku` and `tickets.sku` match `pricing.sku`
- `payments.account` names a `cash_accounts.name`
- `payments.ref_id` is an untyped integer; what it refers to depends on `payments.kind`
- `leases.landlord` and `tickets.requester` are both free text and happen to share the value "Elm City Properties" on ticket 102

## Starting Data Snapshot

Values in the original database, which every reset restores.


- **inventory:** 10 rows across 4 SKUs. Two stock-outs: CC-TEE-WHITE size S (qty 0) and CC-MUG-CREST OS (qty 0).
- **pricing:** CC-HOOD-NAVY 22.00 / 58.00, CC-TEE-WHITE 8.00 / 28.00, CC-HAT-BLUE 6.00 / 22.00, CC-MUG-CREST 3.50 / 14.00 (unit_cost / list_price).
- **vendors:** 1 Bulldog Print Co (apparel reprint, 5 days), 2 Elm City Gifts (mugs and small goods, 3 days), 3 QuickShip CT (local courier, 1 day).
- **leases:** 1 Chapel Street shop, landlord Elm City Properties, 2400.00/month, next due 2026-09-02.
- **cash_accounts:** checking, balance 3400.00, as of 2026-08-31.
- **invoices:** 501, vendor 1, 840.00, due 2026-08-28, status open, "Rush reprint CC-TEE-WHITE S".
- **payments:** empty.

## The Three Tickets (starting state)

All three tickets start with `status = open` and were created on 2026-08-31.

### Ticket 101: Bulldog tee (type `customer_order`)
Requester Tauhid Zaman wants 1 × CC-TEE-WHITE in size S. Inventory shows 0 in size S (M 5, L 3, XL 2). The ticket points at invoice 501, an open 840.00 bill from vendor 1 Bulldog Print Co for a rush reprint of this exact SKU and size, due 2026-08-28 and therefore 3 days overdue as of `date_today`. Because an unpaid invoice blocks that vendor from dispatching, the reprint cannot ship until invoice 501 is paid, and Bulldog Print Co has a 5-day lead time.

### Ticket 102: Rent due (type `rent_notice`)
Requester Elm City Properties, pointing at lease 1 (Chapel Street shop). Monthly rent is 2400.00 and `next_due` is 2026-09-02, two days after `date_today`, matching the note "shop rent due in 2 days." The checking account holds 3400.00.

### Ticket 103: Bulk hoodie discount (type `price_override`)
Requester Yale AI Club wants 20 × CC-HOOD-NAVY in size M with a bulk discount. Inventory holds 8 in size M (S 4, L 14, XL 6), so 12 are short. Pricing gives unit_cost 22.00 and list_price 58.00. The only vendor with an apparel specialty is vendor 1 Bulldog Print Co, which is the same vendor blocked by overdue invoice 501.

### Cross-ticket cash picture
Only outflows are modeled. Rent (2400.00) plus invoice 501 (840.00) total 3240.00 against a 3400.00 balance, leaving 160.00. Any further purchase order would exceed available cash.

## Problem 3: MCP Server Tools

The server lives in `mcp_server/` (FastMCP) and reads only `data/campus_customs_new.db`. These first three tools are read-only, take a `ticket_id`, and judge dates against `desk.date_today`. See `mcp_server/README.md` for layout and how to add tools.

### check_order_fulfillment
- **Purpose:** Report whether a customer order can be filled from stock and, if not, whether the vendor restock it depends on is blocked by unpaid invoices.
- **Reads:** `tickets`, `inventory`, `invoices`, `vendors`, `desk`.
- **Ticket:** 101.
- **Why it fits:** Ticket 101 asks for 1 × CC-TEE-WHITE size S and links to invoice 501; the tool shows size S is at qty 0, that invoice 501 is a 3-day-overdue 840.00 bill to Bulldog Print Co for a rush reprint of that exact tee, and that the unpaid invoice blocks the vendor's 5-day restock.

### check_rent_obligation
- **Purpose:** Report how much rent is due on a lease, when, and whether cash on hand can cover it, without recording any payment.
- **Reads:** `tickets`, `leases`, `cash_accounts`, `desk`.
- **Ticket:** 102.
- **Why it fits:** Ticket 102 is a rent notice from Elm City Properties linked to lease 1; the tool confirms the 2400.00 monthly rent is due 2026-09-02, two days after the shop date, and that the checking balance of 3400.00 can cover it with 1000.00 left.

### evaluate_bulk_discount_request
- **Purpose:** Compute margin at list price and at an optional proposed price, compare stock with the quantity requested, and list which vendors could cover any shortfall and whether they are blocked.
- **Reads:** `tickets`, `pricing`, `inventory`, `vendors`, `invoices`, `desk`.
- **Ticket:** 103.
- **Why it fits:** Ticket 103 asks for 20 × CC-HOOD-NAVY size M at a bulk discount; the tool shows list price 58.00 over unit cost 22.00, only 8 in stock so 12 short, and that the sole apparel vendor (Bulldog Print Co) is blocked by overdue invoice 501.

### Conventions adopted
- An invoice with `status = 'open'` (the only value in the source data) is treated as unpaid and blocks its vendor from dispatching.
- No tool reads `payments` yet because its `kind` and `ref_id` have no defined vocabulary; conventions will be set when write tools are added.
- Update (Problem 5): `payments` conventions are now set; see "Board tables added to the working copy" below.

## Problem 5: Agent Team and MCP Tools

Five PydanticAI agents in `backend/agents/`, one file each. Data types live in `backend/models.py`, the registry and run entry points (`run_agent`, `reset_database`) in `backend/team.py`, the audited agent loop in `backend/runner.py`, and the MCP connection in `backend/mcp_client.py`.

### Model
Every agent shares one model object built in `backend/config.py`: `gpt-6-luna` called directly through OpenAI's Responses API, authenticated with `OPENAI_API_KEY` loaded from `.env`. The key is never hard-coded, logged, or printed. No other model is referenced. The Responses API is used because gpt-6-luna rejects function tools combined with reasoning on the Chat Completions endpoint.

### Agents
System prompts are in `backend/prompts/<agent>.md`, read on every run.

| Agent | Responsibility | MCP tools it can see (plus `delegate`) |
|---|---|---|
| Boss | Reviews each ticket, assigns work to specialists, reconciles findings, makes the final decision. | common, `list_open_tickets`, `update_ticket_status`, `list_payment_requests` |
| Inventory | Stock by SKU and size, shortages, restocking vendors and whether they are blocked. | common, `check_order_fulfillment`, `check_stock`, `list_vendors`, `check_vendor_dispatch`, `create_draft` |
| Accounting | Cash, invoices, margins, payment feasibility; creates payment and purchase order requests for human approval. | common, `get_cash_position`, `list_invoices`, `calculate_margin`, `evaluate_bulk_discount_request`, `list_payments`, `list_payment_requests`, `request_invoice_payment`, `request_rent_payment`, `request_purchase_order`, `check_vendor_dispatch`, `get_lease_details` |
| Facilities | Leases and rent: amounts, due dates, urgency. | common, `check_rent_obligation`, `get_lease_details`, `create_draft` |
| Customer Service | Drafts customer messages from facts and decisions given to it. | common, `create_draft` |

"Common" is `get_shop_date`, `get_ticket`, `list_board_posts`, `post_ticket_note`. Only Accounting can create payment requests. No agent can see `reset_working_database`.

### Board tables added to the working copy
The source schema has nowhere to hold pending payments or drafts, so the MCP server adds two tables to `campus_customs_new.db` only (recreated after every reset; the original is never changed):

- `payment_requests`: every requested invoice, rent, or purchase order payment, with status `pending_approval`, `approved`, `paid`, or `rejected`, who requested it, who decided, and when.
- `board_posts`: drafts, notes, and status changes per ticket.

Conventions for the source `payments` table: `kind` is `invoice`, `rent`, or `purchase_order`; `ref_id` is `invoices.id`, `leases.id`, or `vendors.id` respectively; `paid_at` is `desk.date_today`; `approved_by` is the human approver's name. A paid invoice gets `status = 'paid'`. A paid rent advances `leases.next_due` by one month. A purchase order cost is `pricing.unit_cost` × qty, with expected arrival on shop date + `vendors.lead_days`; inventory is not increased until goods arrive.

### MCP tools (26)

| Tool | Tables | Access |
|---|---|---|
| `check_order_fulfillment(ticket_id)` | tickets, inventory, invoices, vendors, desk | read |
| `check_rent_obligation(ticket_id)` | tickets, leases, cash_accounts, desk | read |
| `evaluate_bulk_discount_request(ticket_id, proposed_unit_price)` | tickets, pricing, inventory, vendors, invoices, desk | read |
| `get_shop_date()` | desk | read |
| `get_ticket(ticket_id)` | tickets | read |
| `list_open_tickets()` | tickets | read |
| `check_stock(sku, size)` | inventory | read |
| `list_vendors()` | vendors, invoices, desk | read |
| `check_vendor_dispatch(vendor_id)` | vendors, invoices, desk | read |
| `get_lease_details(lease_id)` | leases, desk | read |
| `get_cash_position(account)` | cash_accounts, payment_requests | read |
| `list_invoices(status, vendor_id)` | invoices, vendors, payment_requests, desk | read |
| `calculate_margin(sku, unit_price, qty)` | pricing | read |
| `list_payments()` | payments | read |
| `list_payment_requests(status)` | payment_requests | read |
| `request_invoice_payment(invoice_id, ...)` | invoices, cash_accounts, tickets; writes payment_requests | pending request only |
| `request_rent_payment(lease_id, ...)` | leases, cash_accounts, tickets; writes payment_requests | pending request only |
| `request_purchase_order(vendor_id, sku, size, qty, ...)` | vendors, inventory, pricing, invoices, cash_accounts, desk, tickets; writes payment_requests | pending request only |
| `create_draft(ticket_id, ...)` | tickets; writes board_posts | draft only, never sent |
| `post_ticket_note(ticket_id, ...)` | tickets; writes board_posts | write |
| `update_ticket_status(ticket_id, status, ...)` | writes tickets.status, board_posts | write |
| `list_board_posts(ticket_id)` | board_posts | read |
| `reset_working_database()` | all; restores from the original | operator only, hidden from agents |
| `list_tickets()` | tickets | read; backend only, hidden from agents |
| `approve_payment_request(request_id, approver, approval_signature_hex)` | payment_requests, payments, cash_accounts, invoices, leases, desk | human approval from the dashboard; backend only, needs a signature from the backend's secret key |
| `mark_ticket_resolved(ticket_id, run_id)` | tickets; writes board_posts | backend only, hidden from agents; called after a run finishes |

Not a tool: the terminal approval program `python -m mcp_server.approve`, which writes the same tables as `approve_payment_request`.

### Safety
- **Payments need a human, enforced in code.** No MCP tool can approve or execute a payment. Agents can only create `pending_approval` requests. Approval happens only through a human: the dashboard's approve route (below) or `python -m mcp_server.approve`, which refuses to run without an interactive terminal and needs a typed `yes` plus a human name; agent names are refused. Unapproved requests stay pending and nothing is recorded as paid.
- **Dashboard approvals are signed.** `POST /payments/{id}/approve` needs a human name and `human_confirmed: true`, and refuses agent names. The backend signs the request ID and approver name with a random key it makes at startup and passes only to its own MCP server process. `approve_payment_request` refuses any call without a valid signature, so agents and other MCP clients, including Claude Code, cannot approve.
- **Database triggers back this up.** They refuse any `payments` insert without a matching human-approved request, any request created as already approved, any approval that is not from the human source, any jump from pending to paid, and any cash balance below zero.
- **Cash limits.** A request is rejected if it exceeds the account balance or the cash left after other pending requests. Approval re-checks the live balance and rejects if short.
- **Blocked vendors.** A purchase order is rejected while the vendor has an unpaid invoice with no pending payment request, and cannot be approved until that invoice is actually paid.
- **No real contact.** Customer, vendor, and landlord messages are saved only as drafts on the board. No tool sends email or contacts anyone.
- **Facts from the database only.** Dates come from `desk.date_today`; lead times from `vendors`; agents are told never to invent numbers.
- **Clean starting state.** `reset_database()` restores the working copy from the original before each full ticket run. The audit trail is never reset.
- **Audit trail.** `output/audit_trail.json` is an append-only JSON array. It records run start, every model response with its tool calls, every tool result, delegations started, returned, and refused, payment requests, approvals, rejections, resets, and why each run stopped (`final_output`, `usage_limit`, or `error`). Long fields are clipped at 4,000 characters.

### Loop and token limits (`DelegationLimits`, per ticket run)

| Guard | Default | Effect |
|---|---|---|
| `max_depth` | 3 | Refuses a delegation more than 3 levels below the first agent. |
| `max_delegations` | 8 | Refuses further delegations once 8 have run. |
| `allow_reentry` | False | Refuses delegating to an agent already in the chain, which stops ping-pong. |
| self-delegation | always refused | An agent cannot delegate to itself. |
| `request_limit` | 40 | Model requests across the whole run, shared by all sub-runs. |
| `tool_calls_limit` | 60 | Tool calls, including delegations, across the whole run. |
| `total_tokens_limit` | 150,000 | Tokens across the whole run. |

Per-agent tool allowlists also cut tokens, since each request carries only the tool definitions that agent needs. Refusals return to the calling agent as a message. Hitting a usage limit stops the run, which is reported in `stopped_by_limit` and in the audit trail.

## Problem 7: Backend Routes

`backend/main.py` (FastAPI). Start from `backend/` with `uvicorn main:app --reload --port 8000`. Every route reaches shop data through the MCP server; the backend never opens the database. One MCP server process stays open for the app's lifetime.

- GET /desk – the shop date (desk.date_today) for the dashboard clock.
- GET /health – confirms the backend is up.
- GET /tickets – tickets 101, 102, and 103 with their status and a `resolved` flag.
- GET /tickets/{ticket_id} – one ticket with its board drafts, notes, and status changes.
- POST /tickets/{ticket_id}/run – starts the agent team, Boss first, on that ticket in the background and returns a run ID; marks the ticket resolved when the run finishes; never resets the database.
- GET /runs – every run started in this backend session with its status.
- GET /runs/{run_id} – one run's status and, when done, its output, delegations, usage, and stop reason.
- GET /events?ticket_id=&run_id=&limit= – agent events from the audit trail: what each agent said, delegations, tool calls and results, payment decisions, and stop reasons, each with a one-line summary.
- GET /payments/pending – payment and purchase order requests waiting for a human.
- GET /payments – all payment requests plus completed payments.
- POST /payments/{request_id}/approve – a human approves a pending request; body `{"approver_name": "...", "human_confirmed": true}`; this is the only route that changes cash.
- GET /cash – the current checking balance from cash_accounts, plus pending requests and cash left after them.
- POST /reset – restores data/campus_customs_new.db from the original; refused while a run is in progress; the audit trail is kept.

## Problem 8: Dashboard

`frontend/` (React + Vite + TypeScript). Start with `npm run dev` from `frontend/`; it serves on http://localhost:5173 and calls the backend at http://localhost:8000, which allows that origin through CORS. Design choices are in `output/design.md`.

- Lists tickets 101 to 103 in "In" and "Done" trays with their status; a finished run drops the ticket into Done with a stamp.
- Starts the team on the selected ticket and shows live activity: lamps and working animations at each desk, paper airplanes for delegations, and sticky notes for what each agent said and which tools it used.
- Summarizes what each agent did on the selected ticket's latest run.
- Shows pending payment and purchase requests as a paper check; a human types their name to approve through the backend approval route.
- Shows the checking balance in a cash box and refreshes it after an approval; a wall clock shows the shop date.
- A "Reset office" button on the wall calls POST /reset after a confirmation memo; it is locked while a run is in progress and refreshes the trays, cash box, and pending approvals afterward.

## Problem 9: Results

On 2026-10-16 the human operator reset the working database from the dashboard, ran each ticket once through the agent team (gpt-6-luna, live MCP tools), and approved two payments by typing their name on the dashboard check. Agents only filed requests. Cash changed only on those two human approvals.

| Ticket | Boss's last status | Final status | Human approvals | Cash change |
|---|---|---|---|---|
| 101 | awaiting_approval | resolved | request #1, $840.00 to Bulldog Print Co, approved by jae y | $-840.00 |
| 102 | awaiting_approval | resolved | request #2, $2,400.00 to Elm City Properties, approved by jae y | $-2,400.00 |
| 103 | blocked | resolved | none | $0.00 |

- **Checking:** $3,400.00 at the start, $160.00 at the end. The ending balance matches `cash_accounts` in `data/campus_customs_new.db` exactly.
- **Final status:** "resolved" comes from the backend rule that marks a ticket resolved when its run finishes normally. The Boss's own last status is shown beside it.
- **Payment requests:** In both payment tickets, Accounting's first call was rejected by the tool because it passed `requested_by` as "Accounting". It retried in lowercase, and the request went through.
- **Rent approval timing:** The rent approval landed while ticket 102 was still running. The Boss's closing message therefore still calls the rent unpaid, but the database shows it paid.
- **Ticket 103:** The Boss blocked the discount. Restocking the 12 missing hoodies at cost would be $264.00 against $160.00 in checking, and no discount price or authority was given. No purchase order was filed.
- **Loop guard:** It refused four attempts by specialists to delegate back to the Boss. No run hit a usage limit.

Records: `output/audit_trail.json` (every step), `output/resolved_tickets.json` (per-ticket summary), `output/desk_tickets.html` (expected vs. actual, cash), `output/resolved_board.html` (dashboard screenshots).
