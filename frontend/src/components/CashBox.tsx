import { useEffect, useRef, useState } from "react";
import type { Cash } from "../types";

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

function useCountUp(target: number | null) {
  const [shown, setShown] = useState(target ?? 0);
  const from = useRef(target ?? 0);
  useEffect(() => {
    if (target === null) return;
    const start = performance.now(), a = from.current, b = target;
    if (a === b) { setShown(b); return; }
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / 900);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(a + (b - a) * eased);
      if (p < 1) raf = requestAnimationFrame(tick); else from.current = b;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return shown;
}

/** Steel cash box with a counter showing the checking balance. */
export function CashBox({ cash, error, flash }: { cash: Cash | null; error: string | null; flash: boolean }) {
  const shown = useCountUp(cash?.balance ?? null);
  const bills = cash ? Math.max(1, Math.min(7, Math.round(cash.balance / 500))) : 0;
  return (
    <section className={`cashbox ${flash ? "flash" : ""}`} aria-label="Cash box">
      <div className="cashbox-lid" aria-hidden>
        <span className="cashbox-handle" />
      </div>
      <div className="cashbox-body">
        <div className="cashbox-tray" aria-hidden>
          {Array.from({ length: bills }, (_, i) => <span key={i} className="bill" style={{ "--i": i } as React.CSSProperties} />)}
          <span className="coin c1" /><span className="coin c2" /><span className="coin c3" />
        </div>
        <div className="cash-display">
          <span className="cash-label">Checking balance</span>
          <span className="cash-amount" aria-live="polite">{cash ? money(shown) : error ? "Offline" : "…"}</span>
          {cash && <span className="cash-asof">as of {cash.as_of}</span>}
        </div>
        {cash && (
          <dl className="cash-lines">
            <div><dt>Awaiting approval</dt><dd className={cash.pending_total ? "warn" : ""}>{money(cash.pending_total)}</dd></div>
            <div><dt>Left after approvals</dt><dd>{money(cash.available_after_pending)}</dd></div>
          </dl>
        )}
        <div className="cashbox-lock" aria-hidden />
      </div>
    </section>
  );
}
