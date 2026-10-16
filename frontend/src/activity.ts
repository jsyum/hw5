import { AGENTS } from "./agents";
import type { AgentId, AuditEvent } from "./types";

export type DeskState = "idle" | "working" | "waiting";

/** The most recent run on this ticket (by team_run_started). */
export function latestRunId(events: AuditEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].event === "team_run_started" && events[i].run_id) return events[i].run_id!;
  }
  return null;
}

export interface LiveDesk {
  state: DeskState;
  doing: string;
}

/** Who is active right now in a run, and what they are doing. */
export function deskStates(events: AuditEvent[], runId: string | null, running: boolean): Record<AgentId, LiveDesk> {
  const out = Object.fromEntries(AGENTS.map((a) => [a.id, { state: "idle", doing: "At desk" }])) as Record<AgentId, LiveDesk>;
  if (!runId) return out;
  const open: Record<string, number> = {};
  const waitingOn: Record<string, AgentId | null> = {};
  for (const e of events) {
    if (e.run_id !== runId || !e.agent) continue;
    const a = e.agent;
    if (e.event === "agent_run_started") {
      open[a] = (open[a] ?? 0) + 1;
      out[a] = { state: "working", doing: "Reading the request" };
    } else if (["agent_run_finished", "agent_run_stopped", "agent_run_failed"].includes(e.event)) {
      open[a] = Math.max(0, (open[a] ?? 1) - 1);
      out[a] = { state: "idle", doing: e.event !== "agent_run_finished" ? "Stopped"
        : e.depth === 0 ? "Final decision made" : "Handed back findings" };
    } else if (e.event === "model_response") {
      const calls = (e.tool_calls ?? []).filter((c) => c.tool !== "delegate");
      if (calls.length) out[a] = { state: "working", doing: `Using ${calls.map((c) => c.tool).join(", ")}` };
      else if (e.text) out[a] = { state: "working", doing: "Writing a reply" };
    } else if (e.event === "tool_result" && e.tool !== "delegate") {
      out[a] = { state: "working", doing: `Reviewing ${e.tool} results` };
    } else if (e.event === "delegation_started" && e.to_agent) {
      waitingOn[a] = e.to_agent;
      out[a] = { state: "waiting", doing: `Waiting on ${AGENTS.find((x) => x.id === e.to_agent)?.name}` };
    } else if (e.event === "delegation_returned" || e.event === "delegation_refused") {
      waitingOn[a] = null;
      if ((open[a] ?? 0) > 0) out[a] = { state: "working", doing: "Reading the reply" };
    }
  }
  if (!running) {
    for (const a of AGENTS) if (out[a.id].state !== "idle") out[a.id] = { state: "idle", doing: out[a.id].doing };
  }
  return out;
}

export interface AgentSummary {
  agent: AgentId;
  tools: Record<string, number>;
  delegatedTo: AgentId[];
  askedBy: AgentId[];
  paymentRequests: number;
  drafts: number;
  finalWords: string | null;
  sentence: string;
}

const PAYMENT_TOOLS = ["request_invoice_payment", "request_rent_payment", "request_purchase_order"];

export function summarize(events: AuditEvent[], runId: string | null): AgentSummary[] {
  const rows: AgentSummary[] = [];
  if (!runId) return rows;
  const runEvents = events.filter((e) => e.run_id === runId);
  for (const meta of AGENTS) {
    const mine = runEvents.filter((e) => e.agent === meta.id);
    const asked = runEvents.filter((e) => e.event === "delegation_started" && e.to_agent === meta.id);
    if (!mine.length && !asked.length) continue;
    const tools: Record<string, number> = {};
    for (const e of mine) {
      if (e.event !== "model_response") continue;
      for (const c of e.tool_calls ?? []) {
        if (c.tool === "delegate") continue;
        tools[c.tool] = (tools[c.tool] ?? 0) + 1;
      }
    }
    // Count only requests and drafts the tool actually accepted, from the tool results.
    let paymentRequests = 0, drafts = 0;
    for (const e of mine) {
      if (e.event !== "tool_result" || !e.tool || !e.result) continue;
      const res = parseResult(e.result);
      if (PAYMENT_TOOLS.includes(e.tool) && res?.accepted === true) paymentRequests++;
      if (e.tool === "create_draft" && res?.saved === true) drafts++;
    }
    const delegatedTo = [...new Set(mine.filter((e) => e.event === "delegation_started" && e.to_agent).map((e) => e.to_agent!))];
    const askedBy = [...new Set(asked.map((e) => e.agent!).filter(Boolean))];
    const finished = mine.filter((e) => e.event === "agent_run_finished");
    const finalWords = finished.length ? finished[finished.length - 1].output ?? null : null;

    const parts: string[] = [];
    if (askedBy.length) parts.push(`Asked by ${askedBy.map(nameOf).join(" and ")}`);
    const toolNames = Object.keys(tools);
    if (toolNames.length) parts.push(`used ${toolNames.length} tool${toolNames.length > 1 ? "s" : ""}`);
    if (delegatedTo.length) parts.push(`delegated to ${delegatedTo.map(nameOf).join(" and ")}`);
    if (paymentRequests) parts.push(`filed ${paymentRequests} payment request${paymentRequests > 1 ? "s" : ""} for approval`);
    if (drafts) parts.push(`saved ${drafts} draft${drafts > 1 ? "s" : ""}`);
    if (!parts.length) parts.push("Started work");
    const sentence = parts.join(", ").replace(/^./, (c) => c.toUpperCase()) + ".";
    rows.push({ agent: meta.id, tools, delegatedTo, askedBy, paymentRequests, drafts, finalWords, sentence });
  }
  return rows;
}

function parseResult(raw: string): Record<string, unknown> | null {
  try {
    const v = JSON.parse(raw);
    return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function nameOf(id: AgentId): string {
  return AGENTS.find((a) => a.id === id)?.name ?? id;
}
