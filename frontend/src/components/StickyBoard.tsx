import { useState } from "react";
import { AGENT, agentName } from "../agents";
import type { AgentId, AuditEvent } from "../types";
import { renderBold } from "../text";

interface Note {
  key: string;
  agent: AgentId;
  ts: string;
  kind: "said" | "tools" | "delegated" | "refused";
  title: string;
  body: string;
  chips: string[];
}

function toNotes(events: AuditEvent[]): Note[] {
  const notes: Note[] = [];
  for (const e of events) {
    if (!e.agent || !(e.agent in AGENT)) continue;
    const key = `${e.run_id}|${e.ts}|${e.event}|${e.agent}`;
    if (e.event === "model_response") {
      const tools = (e.tool_calls ?? []).filter((c) => c.tool !== "delegate").map((c) => c.tool);
      if (e.text) notes.push({ key, agent: e.agent, ts: e.ts, kind: "said", title: "Says", body: e.text, chips: tools });
      else if (tools.length) notes.push({ key, agent: e.agent, ts: e.ts, kind: "tools", title: "Using tools", body: "", chips: tools });
    } else if (e.event === "delegation_started" && e.to_agent) {
      notes.push({ key, agent: e.agent, ts: e.ts, kind: "delegated", title: `Asks ${agentName(e.to_agent)}`, body: e.task ?? "", chips: [] });
    } else if (e.event === "delegation_refused" && e.to_agent) {
      notes.push({ key, agent: e.agent, ts: e.ts, kind: "refused", title: `Can't hand to ${agentName(e.to_agent)}`, body: e.reason ?? "", chips: [] });
    }
  }
  return notes.reverse();
}

function StickyNote({ n, i }: { n: Note; i: number }) {
  const [open, setOpen] = useState(false);
  const meta = AGENT[n.agent];
  const long = n.body.length > 260;
  const tilt = [-1.6, 1.2, -0.6, 1.8, -1.1, 0.7][i % 6];
  return (
    <article className={`sticky kind-${n.kind}`} style={{ "--paper": meta.paper, "--ink": meta.ink, "--accent": meta.accent, "--tilt": `${tilt}deg` } as React.CSSProperties}>
      <span className="tape" aria-hidden />
      <header>
        <span className="sticky-agent">{meta.name}</span>
        <time>{new Date(n.ts).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" })}</time>
      </header>
      <div className="sticky-title">{n.title}</div>
      {n.body && <p className={`sticky-body ${open || !long ? "" : "clamped"}`}>{renderBold(n.body)}</p>}
      {long && <button className="sticky-more" onClick={() => setOpen(!open)}>{open ? "Show less" : "Read all"}</button>}
      {n.chips.length > 0 && (
        <div className="chips">{n.chips.map((c, k) => <span className="chip" key={k}>{c}</span>)}</div>
      )}
    </article>
  );
}

/** Cork board of sticky notes: each agent writes on its own color. Newest first. */
export function StickyBoard({ events, ticketId }: { events: AuditEvent[]; ticketId: number | null }) {
  const notes = toNotes(events).slice(0, 60);
  return (
    <section className="cork" aria-label="Agent messages">
      <div className="cork-title">
        <span>Message board</span>
        {ticketId && <span className="cork-sub">Ticket #{ticketId}</span>}
      </div>
      <div className="cork-notes" aria-live="polite">
        {notes.length === 0 && <p className="cork-empty">Sticky notes from the team will appear here once they start working.</p>}
        {notes.map((n, i) => <StickyNote key={n.key} n={n} i={i} />)}
      </div>
    </section>
  );
}
