import { useEffect, useState } from "react";
import { AGENT } from "../agents";
import type { PaymentRequest } from "../types";

const ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
  "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
const TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];

function under1000(n: number): string {
  const h = Math.floor(n / 100), r = n % 100;
  const parts: string[] = [];
  if (h) parts.push(`${ONES[h]} hundred`);
  if (r) parts.push(r < 20 ? ONES[r] : TENS[Math.floor(r / 10)] + (r % 10 ? `-${ONES[r % 10]}` : ""));
  return parts.join(" ");
}

export function amountInWords(amount: number): string {
  const dollars = Math.floor(amount + 1e-9);
  const cents = Math.round((amount - dollars) * 100);
  let words = "";
  if (dollars === 0) words = "zero";
  else {
    const th = Math.floor(dollars / 1000), rest = dollars % 1000;
    words = [th ? `${under1000(th)} thousand` : "", rest ? under1000(rest) : ""].filter(Boolean).join(" ");
  }
  return `${words.charAt(0).toUpperCase()}${words.slice(1)} and ${String(cents).padStart(2, "0")}/100 dollars`;
}

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

const KIND: Record<PaymentRequest["kind"], string> = {
  invoice: "Vendor invoice",
  rent: "Rent",
  purchase_order: "Purchase order",
};

interface Props {
  pending: PaymentRequest[];
  shopDate: string | null;
  available: number | null;
  onApprove: (req: PaymentRequest, name: string) => Promise<void>;
}

/** A paper check slides into frame for each pending request; a human signs by typing their name. */
export function CheckPanel({ pending, shopDate, available, onApprove }: Props) {
  const [index, setIndex] = useState(0);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paidId, setPaidId] = useState<number | null>(null);
  const [paidReq, setPaidReq] = useState<PaymentRequest | null>(null);
  const [tucked, setTucked] = useState(false);

  const req = pending[Math.min(index, pending.length - 1)];
  useEffect(() => { if (index >= pending.length) setIndex(Math.max(0, pending.length - 1)); }, [pending.length, index]);
  useEffect(() => { setError(null); }, [req?.id]);
  useEffect(() => { if (pending.length) setTucked(false); }, [pending.length]);

  const visible = (pending.length > 0 || paidId !== null);
  if (!visible) return null;

  if (tucked && pending.length) {
    return (
      <button className="check-tab" onClick={() => setTucked(false)}>
        ✎ {pending.length} check{pending.length > 1 ? "s" : ""} awaiting your signature
      </button>
    );
  }

  const sign = async () => {
    if (!req) return;
    setBusy(true); setError(null);
    try {
      const signed = req;
      setPaidReq(signed);          // keep the signed check on screen for its PAID stamp
      await onApprove(signed, name.trim());
      setPaidId(signed.id);
      window.setTimeout(() => { setPaidId(null); setPaidReq(null); setName(""); }, 1900);
    } catch (e) {
      setPaidReq(null);
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const shown = paidReq ?? req ?? null;
  const validName = name.trim().length >= 2;
  const exceeds = shown && available !== null && shown.amount > available + 1e-9;

  return (
    <aside className="check-dock" aria-label="Payment approval">
      {shown && (
        <div key={shown.id} className={`check ${paidId === shown.id ? "paid" : ""}`}>
          <div className="check-top">
            <div>
              <div className="check-bank">Campus Customs</div>
              <div className="check-acct">Operating account · {shown.account}</div>
            </div>
            <div className="check-meta">
              <div><span>No.</span> {String(shown.id).padStart(4, "0")}</div>
              <div><span>Date</span> {shopDate ?? "—"}</div>
            </div>
          </div>
          <div className="check-row payee-row">
            <span className="check-label">Pay to the order of</span>
            <span className="check-payee">{shown.payee ?? "Payee unknown"}</span>
            <span className="check-amount">{money(shown.amount)}</span>
          </div>
          <div className="check-words">{amountInWords(shown.amount)}</div>
          <div className="check-memo">
            <span className="check-label">Memo</span>
            <span>
              <strong>{KIND[shown.kind]}</strong>
              {shown.ticket_id ? ` · Ticket #${shown.ticket_id}` : ""}
              {shown.kind === "purchase_order" && shown.sku ? ` · ${shown.qty} × ${shown.sku} ${shown.size}` : ""}
              {shown.reason ? ` · ${shown.reason}` : ""}
            </span>
          </div>
          <div className="check-requested">
            Requested by <span style={{ color: AGENT[shown.requested_by]?.accent }}>{AGENT[shown.requested_by]?.name ?? shown.requested_by}</span>
            {shown.expected_arrival ? ` · arrives ${shown.expected_arrival}` : ""}
          </div>
          <form className="check-sign" onSubmit={(e) => { e.preventDefault(); if (validName && !busy) void sign(); }}>
            <label htmlFor={`sig-${shown.id}`} className="check-label">Authorized signature (type your full name)</label>
            <input id={`sig-${shown.id}`} className="signature" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="Your name" autoComplete="name" disabled={busy || paidId === shown.id} />
            <div className="check-actions">
              <button type="submit" className="sign-btn" disabled={!validName || busy || paidId === shown.id}>
                {busy ? "Signing…" : `Sign & approve ${money(shown.amount)}`}
              </button>
              <button type="button" className="ghost-btn" onClick={() => setTucked(true)}>Not now</button>
            </div>
            {exceeds && <p className="check-warn">This is more than the cash in the box. The backend will refuse it.</p>}
            {error && <p className="check-error" role="alert">{error}</p>}
          </form>
          <div className="micr" aria-hidden>⑆0412 0007⑆ 88213 {String(shown.id).padStart(4, "0")}⑈</div>
          {paidId === shown.id && <div className="paid-stamp" aria-hidden>Paid</div>}
        </div>
      )}
      {pending.length > 1 && (
        <div className="check-pager">
          <button className="ghost-btn" onClick={() => setIndex((i) => Math.max(0, i - 1))} disabled={index === 0}>‹ Previous</button>
          <span>Check {Math.min(index, pending.length - 1) + 1} of {pending.length}</span>
          <button className="ghost-btn" onClick={() => setIndex((i) => Math.min(pending.length - 1, i + 1))} disabled={index >= pending.length - 1}>Next ›</button>
        </div>
      )}
    </aside>
  );
}
