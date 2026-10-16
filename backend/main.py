"""Campus Customs FastAPI backend.

Start from the backend/ folder:

    uvicorn main:app --reload --port 8000

Every shop read and write goes through the Campus Customs MCP server; this
module never opens the database. Agent runs never reset the database; only
POST /reset does.
"""

from __future__ import annotations

import asyncio
import json
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:  # allow `uvicorn main:app` from backend/
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field, field_validator  # noqa: E402

from backend.mcp_client import MCP_TOOLSET, approve_as_human, call_operator_tool  # noqa: E402
from backend.models import AGENT_NAMES  # noqa: E402
from backend.team import reset_database, run_agent  # noqa: E402
from mcp_server import audit  # noqa: E402

TICKET_IDS = (101, 102, 103)
EVENT_TYPES_FOR_UI = {
    "team_run_started", "team_run_finished", "team_run_failed",
    "agent_run_started", "agent_run_finished", "agent_run_stopped", "agent_run_failed",
    "model_response", "tool_result", "tool_retry",
    "delegation_started", "delegation_returned", "delegation_refused",
    "payment_requested", "payment_approved_and_recorded", "payment_rejected", "payment_approval_refused",
    "database_reset", "ticket_marked_resolved",
}

RUNS: dict[str, dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with MCP_TOOLSET:  # one MCP server process for the app's lifetime
        yield


app = FastAPI(title="Campus Customs Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def mcp(name: str, args: dict[str, Any] | None = None) -> Any:
    return await call_operator_tool(name, args)


# ------------------------------------------------------------------ tickets

@app.get("/tickets")
async def list_tickets() -> list[dict[str, Any]]:
    """Tickets 101, 102, 103 with their status and whether they are resolved."""
    rows = await mcp("list_tickets")
    return [{**t, "resolved": t["status"] == "resolved"} for t in rows if t["id"] in TICKET_IDS]


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int) -> dict[str, Any]:
    t = await mcp("get_ticket", {"ticket_id": ticket_id})
    if "error" in t:
        raise HTTPException(404, t["error"])
    posts = await mcp("list_board_posts", {"ticket_id": ticket_id})
    return {**t, "resolved": t["status"] == "resolved", "board_posts": posts}


def _ticket_task(ticket_id: int) -> str:
    return (f"Resolve ticket {ticket_id} on the Campus Customs board. Review the ticket, involve the right "
            "specialists, and record your final decision on the board.")


async def _run_ticket(run_id: str, ticket_id: int) -> None:
    try:
        result = await run_agent(_ticket_task(ticket_id), agent="boss", ticket_id=ticket_id, run_id=run_id)
        finished = not result.stopped_by_limit
        if finished:  # a run that finished normally marks its ticket resolved
            await mcp("mark_ticket_resolved", {"ticket_id": ticket_id, "run_id": run_id})
        RUNS[run_id].update(status="finished" if finished else "stopped",
                            finished_at=_now(), result=result.model_dump())
    except Exception as exc:
        RUNS[run_id].update(status="failed", finished_at=_now(), error=f"{type(exc).__name__}: {exc}")


@app.post("/tickets/{ticket_id}/run", status_code=202)
async def run_ticket(ticket_id: int) -> dict[str, Any]:
    """Start the agent team (Boss first) on one ticket. Does not reset the database."""
    t = await mcp("get_ticket", {"ticket_id": ticket_id})
    if "error" in t:
        raise HTTPException(404, t["error"])
    if any(r["ticket_id"] == ticket_id and r["status"] == "running" for r in RUNS.values()):
        raise HTTPException(409, f"ticket {ticket_id} already has a run in progress")
    import uuid
    run_id = uuid.uuid4().hex[:12]
    RUNS[run_id] = {"run_id": run_id, "ticket_id": ticket_id, "status": "running", "started_at": _now()}
    RUNS[run_id]["task"] = asyncio.create_task(_run_ticket(run_id, ticket_id))
    return {k: v for k, v in RUNS[run_id].items() if k != "task"}


@app.get("/runs")
async def list_runs() -> list[dict[str, Any]]:
    return [{k: v for k, v in r.items() if k not in ("task", "result")} for r in RUNS.values()]


@app.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    if run_id not in RUNS:
        raise HTTPException(404, f"run {run_id} not found in this backend session")
    return {k: v for k, v in RUNS[run_id].items() if k != "task"}


# ------------------------------------------------------------------ events

def _summarize(e: dict[str, Any]) -> str:
    ev = e["event"]
    if ev == "model_response":
        parts = []
        if e.get("text"):
            parts.append(f"said: {e['text']}")
        for c in e.get("tool_calls") or []:
            parts.append(f"called {c['tool']}({c['args']})")
        return "; ".join(parts) or "empty response"
    if ev == "tool_result":
        return f"{e.get('tool')} returned: {e.get('result')}"
    if ev == "delegation_started":
        return f"delegated to {e.get('to_agent')}: {e.get('task')}"
    if ev == "delegation_returned":
        return f"{e.get('to_agent')} answered: {e.get('output')}"
    if ev == "delegation_refused":
        return f"delegation to {e.get('to_agent')} refused: {e.get('reason')}"
    if ev == "ticket_marked_resolved":
        return f"ticket {e.get('ticket_id')} marked resolved"
    if ev.endswith(("finished", "stopped", "failed")):
        return f"stop reason: {e.get('stop_reason')}" + (f" ({e.get('detail')})" if e.get("detail") else "")
    return ev.replace("_", " ")


@app.get("/events")
async def events(ticket_id: int | None = None, run_id: str | None = None,
                 limit: int = Query(500, ge=1, le=5000)) -> list[dict[str, Any]]:
    """Agent events from the audit trail: what agents said, delegations, tool calls and results, stop reasons."""
    path = audit.AUDIT_PATH
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for e in entries:
        if e.get("event") not in EVENT_TYPES_FOR_UI:
            continue
        if ticket_id is not None and e.get("ticket_id") != ticket_id and \
                (e.get("request") or {}).get("ticket_id") != ticket_id:
            continue
        if run_id is not None and e.get("run_id") != run_id:
            continue
        out.append({**e, "summary": _summarize(e)})
    return out[-limit:]


# ------------------------------------------------------------------ payments and cash

async def _payee(req: dict[str, Any]) -> str | None:
    """Who a request pays, looked up through MCP (vendor name or landlord)."""
    if req["kind"] == "rent":
        lease = await mcp("get_lease_details", {"lease_id": req["ref_id"]})
        return lease.get("landlord")
    if req.get("vendor_id") is not None:
        vendor = await mcp("check_vendor_dispatch", {"vendor_id": req["vendor_id"]})
        return vendor.get("name")
    return None


@app.get("/payments/pending")
async def pending_payments() -> list[dict[str, Any]]:
    """Payment and purchase order requests waiting for a human, with the payee's name."""
    rows = await mcp("list_payment_requests", {"status": "pending_approval"})
    return [{**r, "payee": await _payee(r)} for r in rows]


@app.get("/payments")
async def payments() -> dict[str, Any]:
    return {"requests": await mcp("list_payment_requests"), "recorded_payments": await mcp("list_payments")}


class ApproveBody(BaseModel):
    approver_name: str = Field(..., min_length=1, description="Full name of the human approving this payment.")
    human_confirmed: bool = Field(..., description="Must be true: set only when a human clicked Approve.")

    @field_validator("approver_name")
    @classmethod
    def _human_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("approver_name is required")
        if v.lower() in AGENT_NAMES or v.lower().replace(" ", "_") in AGENT_NAMES:
            raise ValueError("approver_name must be a human, not an agent")
        return v


@app.post("/payments/{request_id}/approve")
async def approve_payment(request_id: int, body: ApproveBody) -> dict[str, Any]:
    """Human approval: pays a pending request, records it in payments, and deducts cash."""
    if not body.human_confirmed:
        raise HTTPException(400, "human_confirmed must be true")
    result = await approve_as_human(request_id, body.approver_name)
    if not result.get("approved"):
        raise HTTPException(409, result.get("reason", "approval refused"))
    return result


@app.get("/cash")
async def cash() -> dict[str, Any]:
    """Current checking balance from cash_accounts (plus pending requests against it)."""
    rows = await mcp("get_cash_position", {"account": "checking"})
    acct = rows[0]
    if "error" in acct:
        raise HTTPException(404, acct["error"])
    return {"account": acct["name"], "balance": acct["balance"], "as_of": acct["date"],
            "pending_total": acct["pending_total"], "available_after_pending": acct["available_after_pending"]}


# ------------------------------------------------------------------ reset

@app.post("/reset")
async def reset() -> dict[str, Any]:
    """Restore data/campus_customs_new.db from the original. The audit trail is kept."""
    if any(r["status"] == "running" for r in RUNS.values()):
        raise HTTPException(409, "cannot reset while an agent run is in progress")
    return await reset_database()


@app.get("/desk")
async def desk() -> dict[str, Any]:
    """The shop's current date (desk.date_today) for the dashboard clock."""
    return await mcp("get_shop_date")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
