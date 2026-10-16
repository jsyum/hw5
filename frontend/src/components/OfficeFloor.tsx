import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { AGENT, AGENTS } from "../agents";
import type { LiveDesk } from "../activity";
import type { AgentId, AuditEvent } from "../types";
import { Desk } from "./Desk";

interface Flight {
  key: string;
  from: AgentId;
  to: AgentId;
  task: string;
}

interface Props {
  desks: Record<AgentId, LiveDesk>;
  events: AuditEvent[];
  liveRunId: string | null;
}

/** Top-down office floor: Boss's desk on a rug, four specialists below, paper airplanes for delegations. */
export function OfficeFloor({ desks, events, liveRunId }: Props) {
  const floorRef = useRef<HTMLDivElement>(null);
  const deskRefs = useRef<Partial<Record<AgentId, HTMLDivElement | null>>>({});
  const seen = useRef<Set<string> | null>(null);
  const [flights, setFlights] = useState<Flight[]>([]);

  // Launch a plane for each NEW delegation in the live run. History never re-flies.
  useEffect(() => {
    const keys = events
      .filter((e) => e.event === "delegation_started" && e.agent && e.to_agent)
      .map((e) => ({ key: `${e.run_id}|${e.ts}|${e.agent}|${e.to_agent}`, e }));
    if (seen.current === null) {
      seen.current = new Set(keys.map((k) => k.key));
      return;
    }
    const fresh = keys.filter((k) => !seen.current!.has(k.key));
    fresh.forEach((k) => seen.current!.add(k.key));
    const toFly = fresh.filter((k) => k.e.run_id === liveRunId);
    if (toFly.length) {
      setFlights((f) => [...f, ...toFly.map((k) => ({ key: k.key, from: k.e.agent!, to: k.e.to_agent!, task: k.e.task ?? "" }))]);
    }
  }, [events, liveRunId]);

  return (
    <section className="floor" ref={floorRef} aria-label="Office floor plan">
      <div className="floor-label">Back office · floor plan</div>
      <div className="rug">
        <Desk meta={AGENT.boss} live={desks.boss} big ref={(el) => { deskRefs.current.boss = el; }} />
      </div>
      <div className="desk-grid">
        {AGENTS.filter((a) => a.id !== "boss").map((a) => (
          <Desk key={a.id} meta={a} live={desks[a.id]} ref={(el) => { deskRefs.current[a.id] = el; }} />
        ))}
      </div>
      <div className="plant plant-left" aria-hidden />
      <div className="plant plant-right" aria-hidden />
      <div className="flight-layer" aria-hidden>
        {flights.map((f) => (
          <PaperAirplane
            key={f.key}
            flight={f}
            floor={floorRef.current}
            fromEl={deskRefs.current[f.from] ?? null}
            toEl={deskRefs.current[f.to] ?? null}
            onDone={() => setFlights((all) => all.filter((x) => x.key !== f.key))}
          />
        ))}
      </div>
    </section>
  );
}

function center(el: HTMLElement, floor: HTMLElement) {
  const r = el.getBoundingClientRect();
  const fr = floor.getBoundingClientRect();
  return { x: r.left - fr.left + r.width / 2, y: r.top - fr.top + r.height / 2 };
}

function PaperAirplane({ flight, floor, fromEl, toEl, onDone }: {
  flight: Flight; floor: HTMLElement | null; fromEl: HTMLElement | null; toEl: HTMLElement | null; onDone: () => void;
}) {
  const planeRef = useRef<HTMLDivElement>(null);
  const [label, setLabel] = useState<{ x: number; y: number } | null>(null);

  useLayoutEffect(() => {
    if (!floor || !fromEl || !toEl || !planeRef.current) { onDone(); return; }
    const a = center(fromEl, floor);
    const b = center(toEl, floor);
    const dx = b.x - a.x, dy = b.y - a.y;
    const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
    const lift = Math.max(60, Math.hypot(dx, dy) * 0.25);
    const mid = { x: a.x + dx / 2, y: a.y + dy / 2 - lift };
    setLabel({ x: mid.x, y: mid.y - 26 });
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const anim = planeRef.current.animate(
      [
        { transform: `translate(${a.x}px, ${a.y}px) rotate(${angle - 20}deg) scale(0.7)`, opacity: 0 },
        { transform: `translate(${a.x + dx * 0.15}px, ${a.y + dy * 0.15 - lift * 0.5}px) rotate(${angle - 25}deg) scale(1)`, opacity: 1, offset: 0.15 },
        { transform: `translate(${mid.x}px, ${mid.y}px) rotate(${angle}deg) scale(1.15)`, opacity: 1, offset: 0.5 },
        { transform: `translate(${b.x - dx * 0.08}px, ${b.y - dy * 0.08}px) rotate(${angle + 18}deg) scale(0.95)`, opacity: 1, offset: 0.88 },
        { transform: `translate(${b.x}px, ${b.y}px) rotate(${angle + 25}deg) scale(0.6)`, opacity: 0 },
      ],
      { duration: reduce ? 600 : 1900, easing: "cubic-bezier(.45,.05,.4,1)", fill: "forwards" },
    );
    anim.onfinish = onDone;
    return () => anim.cancel();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const from = AGENT[flight.from], to = AGENT[flight.to];
  return (
    <>
      <div className="plane" ref={planeRef} style={{ "--accent": from.accent } as React.CSSProperties}>
        <svg viewBox="0 0 48 48" width="44" height="44">
          <path d="M4 22 L44 6 L30 42 L22 28 Z" fill="#ffffff" stroke="#7a7466" strokeWidth="1.6" strokeLinejoin="round" />
          <path d="M22 28 L44 6 L18 25 Z" fill="#e9e4d6" stroke="#7a7466" strokeWidth="1.2" strokeLinejoin="round" />
          <path d="M22 28 L24 36 L30 42" fill="none" stroke="#7a7466" strokeWidth="1.2" />
        </svg>
      </div>
      {label && (
        <div className="plane-label" style={{ left: label.x, top: label.y }}>
          <span style={{ color: from.accent }}>{from.name}</span> → <span style={{ color: to.accent }}>{to.name}</span>
        </div>
      )}
    </>
  );
}
