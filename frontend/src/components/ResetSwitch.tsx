import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface Props {
  disabled: boolean;
  onReset: () => Promise<void>;
}

/** Wall-mounted reset button on a brass plate, with a memo-style confirmation card. */
export function ResetSwitch({ disabled, onReset }: Props) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => { if (confirming) cancelRef.current?.focus(); }, [confirming]);
  useEffect(() => { if (disabled) setConfirming(false); }, [disabled]);
  useEffect(() => {
    if (!confirming) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setConfirming(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [confirming]);

  const doReset = async () => {
    setBusy(true); setMsg(null);
    try {
      await onReset();
      setMsg({ kind: "ok", text: "Office reset to the starting data." });
      setConfirming(false);
      window.setTimeout(() => setMsg(null), 3500);
    } catch (e) {
      setMsg({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="reset-wrap">
      <div className="reset-plate">
        <button
          className="reset-btn"
          onClick={() => { setMsg(null); setConfirming(true); }}
          disabled={disabled || busy}
          aria-haspopup="dialog"
          title={disabled ? "Wait for the team to finish before resetting" : "Restore the starting shop data"}
        >
          <span className="reset-cap" aria-hidden />
          <span className="reset-text">{busy ? "Resetting…" : "Reset office"}</span>
        </button>
        <span className="reset-caption">{disabled ? "Locked while agents work" : "Restores starting data"}</span>
      </div>
      {msg && <p className={`reset-msg ${msg.kind}`} role="status">{msg.text}</p>}

      {confirming && createPortal(
        <div className="memo-backdrop" onClick={() => !busy && setConfirming(false)}>
          <div className="memo" role="alertdialog" aria-modal="true" aria-labelledby="memo-title" aria-describedby="memo-body"
            onClick={(e) => e.stopPropagation()}>
            <span className="memo-pin" aria-hidden />
            <div className="memo-head">MEMO</div>
            <h2 id="memo-title">Reset the office?</h2>
            <p id="memo-body">
              This restores the shop's starting data: all three tickets go back to <strong>Open</strong>, the checking balance
              returns to its original amount, and pending payment requests, drafts, and notes are cleared. The audit trail is kept.
            </p>
            {msg?.kind === "err" && <p className="memo-error" role="alert">{msg.text}</p>}
            <div className="memo-actions">
              <button className="memo-confirm" onClick={() => void doReset()} disabled={busy}>
                {busy ? "Resetting…" : "Yes, reset everything"}
              </button>
              <button className="ghost-btn" ref={cancelRef} onClick={() => setConfirming(false)} disabled={busy}>Cancel</button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
