# Campus Customs: AI Agent Team

A team of five AI agents runs the back office of Campus Customs, a campus apparel shop, through a shared ticket board. The project has three connected parts:

- **MCP server** (`mcp_server/`, FastMCP): the only route to the shop database, exposing 26 tools.
- **FastAPI backend** (`backend/`): hosts the PydanticAI agent team (Boss, Inventory, Accounting, Facilities, Customer Service) and the API routes.
- **React dashboard** (`frontend/`, React + Vite + TypeScript): an office-themed view for human oversight and payment approval.

## Model provider: OpenAI instead of Portkey

The assignment originally specified Portkey. **Per Professor Zaman, who provided an OpenAI API key because of a Portkey access issue, all model calls go directly to OpenAI instead of Portkey.** The model is still `gpt-6-luna` only, and no other model is used anywhere. It is called through OpenAI's Responses API, because gpt-6-luna rejects function tools combined with reasoning on the Chat Completions endpoint. The key is read from `.env` and is never hard-coded, logged, or printed.

## Prerequisites

- Python 3 (tested with 3.15)
- Node.js 24 LTS and npm
- An OpenAI API key with access to `gpt-6-luna`

## Setup

From the project root:

```bash
# 1. Python environment and dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. API key: copy the template, then paste your key into .env
cp .env.example .env

# 3. Dashboard dependencies
cd frontend && npm install && cd ..
```

`.env` must contain one line, `OPENAI_API_KEY=...`. It is listed in `.gitignore` and is never committed.

## Databases

| File | Role |
|---|---|
| `data/campus_customs.db` | Original data. Never modified. |
| `data/campus_customs_new.db` | Working copy that every tool reads and writes. |

The committed working copy holds the state **after** the graded run: all three tickets resolved, checking at $160.00. Restore it to the starting values before you reproduce anything.

**Option A, plain copy:**

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

**Option B, the project's reset function:** this does the same copy with SQLite's backup API and recreates the board tables.

```bash
python -c "from mcp_server.db import reset_working_db; print(reset_working_db())"
```

After either option, checking is $3,400.00 and tickets 101, 102, and 103 are open. The MCP server adds its board tables (`payment_requests`, `board_posts`) and safety triggers to the working copy automatically when it starts.

## Running the project

Use three terminals, each with the virtual environment active (`source .venv/bin/activate`).

**1. MCP server.** The backend starts its own MCP server process automatically, so this step is optional. To run the server on its own over stdio:

```bash
python -m mcp_server.server
```

Claude Code also launches it automatically from `.mcp.json` when opened in the project root. That config uses `.venv/bin/python`, so create the virtual environment first.

**2. FastAPI backend:** serves on http://localhost:8000.

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**3. React dashboard:** opens at http://localhost:5173.

```bash
cd frontend
npm run dev
```

## Full ticket resolution run

1. **Reset the database first.** Use the red **Reset office** button on the dashboard wall, or run:

   ```bash
   curl -X POST http://localhost:8000/reset
   ```

   Running a ticket never resets the database, and reset is refused while a run is in progress. Note the starting balance in the cash box, which should be $3,400.00.
2. **Run a ticket.** Click a ticket in the **In** tray, then **Start agent team**. You can watch the run live: desk lamps show who is working, paper airplanes show delegations, and sticky notes show what each agent says and which tools it uses. When the run finishes, the ticket drops into the **Done** tray.
3. **Approve payments.** When an agent files a payment request, a paper check slides in. Type your name and click **Sign & approve**. This is the only step that moves money, and the cash box updates right away. You can also approve from a terminal with `python -m mcp_server.approve`.
4. Repeat for tickets 101, 102, and 103.

## Safety rules

- **Payments need a human.** No MCP tool can approve or execute a payment. Agents can only create `pending_approval` requests.
- **Approval is enforced in code.** The dashboard's approve route requires a human name and a confirmation flag. It is signed with a per-process secret that agents and other MCP clients never see. Database triggers also reject any payment without a human-approved request, and any balance below zero.
- **Cash limits.** A request is rejected if it exceeds the cash left after other pending requests.
- **No real contact.** Customer, vendor, and landlord messages are saved as drafts on the board and never sent.
- **Dates come from the shop.** `desk.date_today` is the current date; lead times come from the `vendors` table.
- **Bounded runs.** Each run is capped at 3 levels of delegation, 8 delegations, 40 model requests, 60 tool calls, and 150,000 tokens.
- **Audit trail.** Every agent step, tool call, delegation, approval, and reset is appended to `output/audit_trail.json`, which is never reset.

## API routes

| Route | What it does |
|---|---|
| `GET /tickets` | Tickets 101 to 103 with status |
| `POST /tickets/{id}/run` | Start the agent team on a ticket |
| `GET /runs/{run_id}` | Run status and result |
| `GET /events?ticket_id=` | Agent activity from the audit trail |
| `GET /payments/pending` | Requests waiting for a human |
| `POST /payments/{id}/approve` | Human approval, the only route that moves cash |
| `GET /cash` | Checking balance |
| `GET /desk` | Shop date |
| `POST /reset` | Restore the working database |

`output/harness.md` lists every route, tool, table, and agent in detail.

## Project layout

```
AI_prompts.md          Every prompt given to the coding assistant, per problem
requirements.txt       Python dependencies
.env.example           Template for .env (placeholder key only)
.mcp.json              MCP server config for Claude Code
data/                  Original and working SQLite databases
mcp_server/            FastMCP server: tools, payment approval, audit writer (see mcp_server/README.md)
backend/               FastAPI app (main.py), agents, models.py, prompts/
frontend/              React + Vite + TypeScript dashboard
output/                Deliverables (below)
```

## Deliverables in `output/`

| File | Contents |
|---|---|
| `harness.md` | Tables, MCP tools, agents, routes, dashboard, safety rules, and results |
| `mcp_smoke.json` | Smoke test of the first three MCP tools through Claude Code |
| `desk_tickets.html` | Expected versus actual per ticket, cash walk-through, and reflection. Open it in a browser. |
| `design.md` | Dashboard design choices |
| `resolved_tickets.json` | Per-ticket outcome, agent contributions, and human approvals |
| `resolved_board.html` | Dashboard screenshots of each resolved ticket |
| `audit_trail.json` | Append-only log of every run |
| `github_url.txt` | URL of this repository |

## Results of the graded run

| Ticket | Outcome | Cash change |
|---|---|---|
| 101 | Invoice 501 paid after human approval, unblocking the vendor | −$840.00 |
| 102 | Rent paid after human approval | −$2,400.00 |
| 103 | Discount not approved: 12 hoodies short, and the restock was not affordable | $0.00 |

Checking went from $3,400.00 to $160.00. `output/desk_tickets.html` and `output/resolved_tickets.json` have the full details.
