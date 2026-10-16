import type { RunInfo, Ticket } from "../types";
import { statusLabel } from "./Trays";

interface Props {
  ticket: Ticket | null;
  run: RunInfo | null;
  starting: boolean;
  error: string | null;
  onStart: () => void;
}

/** Manila folder for the selected ticket, with the button that starts the agent team. */
export function TicketFolder({ ticket, run, starting, error, onStart }: Props) {
  if (!ticket) return <section className="folder"><p className="muted">Pick a ticket from a tray.</p></section>;
  const running = run?.status === "running";
  const st = statusLabel(ticket, running);
  const facts: [string, string][] = [];
  if (ticket.sku) facts.push(["Item", `${ticket.qty ?? "?"} × ${ticket.sku}${ticket.size ? ` size ${ticket.size}` : ""}`]);
  if (ticket.invoice_id) facts.push(["Invoice", `#${ticket.invoice_id}`]);
  if (ticket.lease_id) facts.push(["Lease", `#${ticket.lease_id}`]);
  facts.push(["Requester", ticket.requester]);

  let buttonText = "Start agent team";
  if (starting) buttonText = "Handing it to the Boss…";
  else if (running) buttonText = "Team is working…";
  else if (ticket.resolved) buttonText = "Ticket resolved";

  return (
    <section className="folder" aria-label={`Ticket ${ticket.id} folder`}>
      <div className="folder-tab">Ticket #{ticket.id}</div>
      <div className="folder-body">
        <div className="folder-head">
          <h2>{ticket.subject}</h2>
          <span className={`status-pill ${st.cls}`}>{st.text}</span>
        </div>
        {ticket.notes && <p className="folder-note">“{ticket.notes}”</p>}
        <dl className="folder-facts">
          {facts.map(([k, v]) => (
            <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
          ))}
        </dl>
        <button className="start-btn" onClick={onStart} disabled={starting || running || ticket.resolved}>
          {(starting || running) && <span className="spinner" aria-hidden />}
          {buttonText}
        </button>
        {run && run.status !== "running" && (
          <p className={`run-result ${run.status}`}>
            Last run {run.status === "finished" ? "finished" : run.status === "stopped" ? "stopped at a usage limit" : "failed"}
            {run.error ? `: ${run.error}` : "."}
          </p>
        )}
        {error && <p className="run-result failed" role="alert">{error}</p>}
      </div>
    </section>
  );
}
