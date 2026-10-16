import { forwardRef } from "react";
import type { AgentMeta } from "../agents";
import type { LiveDesk } from "../activity";

interface Props {
  meta: AgentMeta;
  live: LiveDesk;
  big?: boolean;
}

/** One agent's desk seen from above: desk top, monitor, papers, lamp, chair, brass nameplate. */
export const Desk = forwardRef<HTMLDivElement, Props>(function Desk({ meta, live, big }, ref) {
  const on = live.state !== "idle";
  return (
    <div
      className={`desk-station ${big ? "desk-big" : ""} state-${live.state}`}
      style={{ "--accent": meta.accent, "--paper": meta.paper, "--ink": meta.ink } as React.CSSProperties}
      aria-label={`${meta.name} desk, ${live.state === "idle" ? "idle" : live.state === "waiting" ? "waiting" : "working"}`}
    >
      <div className="desk-scene" ref={ref}>
        <div className={`lamp-glow ${on ? "on" : ""}`} aria-hidden />
        <div className="desk-top" aria-hidden>
          <div className={`monitor ${on ? "on" : ""}`}>
            <span className="screen-line l1" />
            <span className="screen-line l2" />
            <span className="screen-line l3" />
          </div>
          <div className="keyboard" />
          <div className="papers">
            <span className="paper p1" />
            <span className="paper p2" />
            <span className={`pen ${live.state === "working" ? "writing" : ""}`} />
          </div>
          <div className="mug" />
          <div className={`lamp ${on ? "on" : ""}`}>
            <span className="lamp-bulb" />
          </div>
          <div className="nameplate">
            <span>{meta.name}</span>
          </div>
        </div>
        <div className={`chair ${live.state === "working" ? "busy" : ""}`} aria-hidden>
          <div className="person">{meta.initials}</div>
        </div>
      </div>
      <div className="desk-status">
        <span className={`status-dot ${live.state}`} aria-hidden />
        <span className="status-text">
          <strong>{live.state === "idle" ? "Idle" : live.state === "waiting" ? "Waiting" : "Working"}</strong>
          <span className="status-doing">{live.doing}</span>
        </span>
      </div>
    </div>
  );
});
