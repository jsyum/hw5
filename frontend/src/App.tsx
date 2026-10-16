import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, API_BASE } from "./api";
import { deskStates, latestRunId, summarize } from "./activity";
import { usePolling } from "./usePolling";
import type { AuditEvent, PaymentRequest, RunInfo, Ticket } from "./types";
import { AgentSummaryCards } from "./components/AgentSummary";
import { CashBox } from "./components/CashBox";
import { CheckPanel } from "./components/CheckPanel";
import { OfficeFloor } from "./components/OfficeFloor";
import { ResetSwitch } from "./components/ResetSwitch";
import { StickyBoard } from "./components/StickyBoard";
import { TicketFolder } from "./components/TicketFolder";
import { Trays } from "./components/Trays";
import { WallClock } from "./components/WallClock";

export default function App() {
  const [selectedId, setSelectedId] = useState<number | null>(101);
  const [runs, setRuns] = useState<Record<number, RunInfo>>({});
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [justResolved, setJustResolved] = useState<Set<number>>(new Set());
  const [cashFlash, setCashFlash] = useState(false);
  const prevResolved = useRef<Map<number, boolean> | null>(null);

  const anyRunning = Object.values(runs).some((r) => r.status === "running");
  const runningIds = useMemo(() => new Set(Object.values(runs).filter((r) => r.status === "running").map((r) => r.ticket_id)), [runs]);

  const tickets = usePolling<Ticket[]>(api.tickets, anyRunning ? 1500 : 4000);
  const desk = usePolling(api.desk, 60000);
  const cash = usePolling(api.cash, anyRunning ? 2000 : 5000);
  const pending = usePolling<PaymentRequest[]>(api.pending, anyRunning ? 1500 : 4000);
  const selectedRunning = selectedId !== null && runningIds.has(selectedId);
  const events = usePolling<AuditEvent[]>(
    () => (selectedId === null ? Promise.resolve([]) : api.events(selectedId)),
    selectedRunning ? 900 : 4000,
    [selectedId],
  );

  // Pick up runs already in progress (e.g. after a page reload).
  useEffect(() => {
    api.runs().then((rs) => {
      const m: Record<number, RunInfo> = {};
      for (const r of rs) if (!m[r.ticket_id] || r.started_at > m[r.ticket_id].started_at) m[r.ticket_id] = r;
      setRuns(m);
    }).catch(() => undefined);
  }, []);

  // Poll each running run until it ends. Refs keep this timer stable across re-renders.
  const runsRef = useRef(runs);
  runsRef.current = runs;
  const refreshAll = useRef<() => void>(() => undefined);
  refreshAll.current = () => { void tickets.refresh(); void events.refresh(); void cash.refresh(); void pending.refresh(); };
  useEffect(() => {
    if (!anyRunning) return;
    const id = window.setInterval(async () => {
      for (const r of Object.values(runsRef.current)) {
        if (r.status !== "running") continue;
        try {
          const fresh = await api.run(r.run_id);
          if (fresh.status !== "running") {
            setRuns((m) => ({ ...m, [fresh.ticket_id]: fresh }));
            refreshAll.current();
          }
        } catch { /* backend restarted; keep polling tickets */ }
      }
    }, 1200);
    return () => window.clearInterval(id);
  }, [anyRunning]);

  // Detect tickets that just became resolved so they can drop into the Done tray with a stamp.
  useEffect(() => {
    if (!tickets.data) return;
    const now = new Map(tickets.data.map((t) => [t.id, t.resolved]));
    if (prevResolved.current) {
      const fresh = tickets.data.filter((t) => t.resolved && prevResolved.current!.get(t.id) === false).map((t) => t.id);
      if (fresh.length) {
        setJustResolved((s) => new Set([...s, ...fresh]));
        window.setTimeout(() => setJustResolved((s) => { const n = new Set(s); fresh.forEach((id) => n.delete(id)); return n; }), 2600);
      }
    }
    prevResolved.current = now;
  }, [tickets.data]);

  const startRun = useCallback(async () => {
    if (selectedId === null) return;
    setStarting(true); setStartError(null);
    try {
      const r = await api.startRun(selectedId);
      setRuns((m) => ({ ...m, [r.ticket_id]: r }));
      void events.refresh();
    } catch (e) {
      setStartError(e instanceof Error ? e.message : String(e));
    } finally {
      setStarting(false);
    }
  }, [selectedId, events]);

  const approve = useCallback(async (req: PaymentRequest, name: string) => {
    await api.approve(req.id, name);
    await Promise.all([cash.refresh(), pending.refresh(), events.refresh()]);
    setCashFlash(true);
    window.setTimeout(() => setCashFlash(false), 1400);
  }, [cash, pending, events]);

  const resetOffice = useCallback(async () => {
    await api.reset();
    setStartError(null);
    await Promise.all([tickets.refresh(), cash.refresh(), pending.refresh(), events.refresh()]);
  }, [tickets, cash, pending, events]);

  const ev = events.data ?? [];
  const selected = tickets.data?.find((t) => t.id === selectedId) ?? null;
  const run = selectedId !== null ? runs[selectedId] ?? null : null;
  const runId = run?.run_id ?? latestRunId(ev);
  const desks = useMemo(() => deskStates(ev, runId, selectedRunning), [ev, runId, selectedRunning]);
  const summary = useMemo(() => summarize(ev, runId), [ev, runId]);
  const backendDown = tickets.error && !tickets.data;

  return (
    <div className="office">
      <header className="wall">
        <div className="sign">
          <span className="sign-name">Campus Customs</span>
          <span className="sign-sub">Back office · agent team</span>
        </div>
        <WallClock shopDate={desk.data?.shop_date ?? null} />
        <div className="wall-right">
          <div className="legend" aria-label="Legend">
            <span><i className="status-dot working" /> Working</span>
            <span><i className="status-dot waiting" /> Waiting on a teammate</span>
            <span><i className="status-dot idle" /> Idle</span>
          </div>
          <ResetSwitch disabled={anyRunning || starting} onReset={resetOffice} />
        </div>
      </header>

      {backendDown && (
        <div className="banner" role="alert">
          Can't reach the backend at {API_BASE}. Start it from <code>backend/</code> with
          <code>uvicorn main:app --reload --port 8000</code>.
        </div>
      )}

      <main className="room">
        <div className="col-left">
          <Trays tickets={tickets.data ?? []} selectedId={selectedId} runningIds={runningIds}
            justResolved={justResolved} onSelect={(id) => { setSelectedId(id); setStartError(null); }} />
          <TicketFolder ticket={selected} run={run} starting={starting} error={startError} onStart={startRun} />
        </div>
        <div className="col-center">
          <OfficeFloor desks={desks} events={ev} liveRunId={selectedRunning ? runId : null} />
          <AgentSummaryCards rows={summary} runId={runId} runStatus={run?.status ?? null} />
        </div>
        <div className="col-right">
          <CashBox cash={cash.data} error={cash.error} flash={cashFlash} />
          <StickyBoard events={ev} ticketId={selectedId} />
        </div>
      </main>

      <CheckPanel pending={pending.data ?? []} shopDate={desk.data?.shop_date ?? null}
        available={cash.data?.balance ?? null} onApprove={approve} />
    </div>
  );
}
