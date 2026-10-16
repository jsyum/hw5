import { useState } from "react";
import { AGENT } from "../agents";
import type { AgentSummary } from "../activity";
import { renderBold } from "../text";

/** Index cards: a short account of what each agent did on the selected ticket's latest run. */
export function AgentSummaryCards({ rows, runId, runStatus }: { rows: AgentSummary[]; runId: string | null; runStatus: string | null }) {
  return (
    <section className="summary" aria-label="What each agent did">
      <div className="section-head">
        <h3>Who did what</h3>
        {runId && <span className="muted">Latest run {runId}{runStatus ? ` · ${runStatus}` : ""}</span>}
      </div>
      {rows.length === 0 ? (
        <p className="muted summary-empty">No agent has worked this ticket yet. Start the team to see each agent's part.</p>
      ) : (
        <div className="summary-grid">
          {rows.map((r) => <SummaryCard key={r.agent} r={r} />)}
        </div>
      )}
    </section>
  );
}

function SummaryCard({ r }: { r: AgentSummary }) {
  const [open, setOpen] = useState(false);
  const meta = AGENT[r.agent];
  const tools = Object.entries(r.tools);
  const long = (r.finalWords?.length ?? 0) > 220;
  return (
    <article className="index-card" style={{ "--accent": meta.accent, "--paper": meta.paper, "--ink": meta.ink } as React.CSSProperties}>
      <header>
        <span className="card-badge">{meta.initials}</span>
        <div>
          <div className="card-name">{meta.name}</div>
          <div className="card-role">{meta.role}</div>
        </div>
      </header>
      <p className="card-sentence">{r.sentence}</p>
      {tools.length > 0 && (
        <div className="chips">
          {tools.map(([t, n]) => <span className="chip" key={t}>{t}{n > 1 ? ` ×${n}` : ""}</span>)}
        </div>
      )}
      {r.finalWords && (
        <>
          <p className={`card-final ${open || !long ? "" : "clamped"}`}><strong>Reported: </strong>{renderBold(r.finalWords)}</p>
          {long && <button className="sticky-more" onClick={() => setOpen(!open)}>{open ? "Show less" : "Read all"}</button>}
        </>
      )}
    </article>
  );
}
