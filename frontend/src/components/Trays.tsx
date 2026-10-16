import type { Ticket } from "../types";

interface Props {
  tickets: Ticket[];
  selectedId: number | null;
  runningIds: Set<number>;
  justResolved: Set<number>;
  onSelect: (id: number) => void;
}

const TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Discount request",
};

export function statusLabel(t: Ticket, running: boolean): { text: string; cls: string } {
  if (running) return { text: "Agents working", cls: "running" };
  if (t.resolved) return { text: "Resolved", cls: "resolved" };
  if (t.status === "open") return { text: "Open", cls: "open" };
  return { text: t.status.replace(/_/g, " "), cls: "progress" };
}

function TicketSlip({ t, selected, running, dropping, onSelect }: {
  t: Ticket; selected: boolean; running: boolean; dropping: boolean; onSelect: () => void;
}) {
  const st = statusLabel(t, running);
  return (
    <button
      className={`slip ${selected ? "selected" : ""} ${t.resolved ? "done" : ""} ${dropping ? "dropping" : ""} ${running ? "is-running" : ""}`}
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`Ticket ${t.id}, ${t.subject}, ${st.text}`}
    >
      {selected && <span className="paperclip" aria-hidden />}
      <span className="slip-top">
        <span className="slip-id">#{t.id}</span>
        <span className={`status-pill ${st.cls}`}>{st.text}</span>
      </span>
      <span className="slip-subject">{t.subject}</span>
      <span className="slip-meta">{TYPE_LABEL[t.type] ?? t.type} · {t.requester}</span>
      {t.resolved && <span className={`stamp ${dropping ? "slam" : ""}`} aria-hidden>Resolved</span>}
    </button>
  );
}

/** Wooden letter trays: "In" holds open tickets, "Done" holds resolved ones. */
export function Trays({ tickets, selectedId, runningIds, justResolved, onSelect }: Props) {
  const open = tickets.filter((t) => !t.resolved);
  const done = tickets.filter((t) => t.resolved);
  const tray = (title: string, sub: string, items: Ticket[], kind: "in" | "done") => (
    <div className={`tray tray-${kind}`}>
      <div className="tray-label">
        <span className="tray-title">{title}</span>
        <span className="tray-count">{items.length} {sub}</span>
      </div>
      <div className="tray-bed">
        {items.length === 0 && <p className="tray-empty">{kind === "in" ? "Nothing waiting. Nice." : "No resolved tickets yet."}</p>}
        {items.map((t) => (
          <TicketSlip key={t.id} t={t} selected={t.id === selectedId} running={runningIds.has(t.id)}
            dropping={kind === "done" && justResolved.has(t.id)} onSelect={() => onSelect(t.id)} />
        ))}
      </div>
    </div>
  );
  return (
    <section className="trays" aria-label="Ticket trays">
      {tray("In", open.length === 1 ? "ticket" : "tickets", open, "in")}
      {tray("Done", done.length === 1 ? "ticket" : "tickets", done, "done")}
    </section>
  );
}
