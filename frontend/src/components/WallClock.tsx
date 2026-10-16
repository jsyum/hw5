import { useEffect, useState } from "react";

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

/** Wall clock. The hands tick with local time; the date window and plaque show the SHOP date. */
export function WallClock({ shopDate }: { shopDate: string | null }) {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);
  const h = now.getHours() % 12, m = now.getMinutes(), s = now.getSeconds();
  const [y, mo, d] = shopDate ? shopDate.split("-").map(Number) : [0, 0, 0];
  const pretty = shopDate
    ? new Date(y, mo - 1, d).toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" })
    : "Loading…";

  return (
    <div className="clock-wrap" aria-label={`Shop date ${pretty}`}>
      <svg className="clock" viewBox="0 0 120 120" role="img" aria-hidden>
        <defs>
          <radialGradient id="clockface" cx="50%" cy="45%" r="60%">
            <stop offset="0%" stopColor="#fffdf6" />
            <stop offset="100%" stopColor="#efe8d6" />
          </radialGradient>
        </defs>
        <circle cx="60" cy="60" r="57" fill="#3b2f22" />
        <circle cx="60" cy="60" r="52" fill="url(#clockface)" stroke="#b08d48" strokeWidth="2" />
        {Array.from({ length: 60 }, (_, i) => {
          const a = (i * Math.PI) / 30;
          const major = i % 5 === 0;
          const r1 = major ? 42 : 46, r2 = 49;
          return <line key={i} x1={60 + r1 * Math.sin(a)} y1={60 - r1 * Math.cos(a)} x2={60 + r2 * Math.sin(a)} y2={60 - r2 * Math.cos(a)}
            stroke="#3b2f22" strokeWidth={major ? 2.4 : 0.9} strokeLinecap="round" />;
        })}
        <rect x="66" y="53" width="33" height="14" rx="2" fill="#fff" stroke="#3b2f22" strokeWidth="1" />
        <text x="82.5" y="63.3" textAnchor="middle" fontSize="8.2" fontWeight="700" fill="#8a1c1c" fontFamily="ui-monospace, Menlo, monospace">
          {shopDate ? `${MONTHS[mo - 1]} ${d}` : "--"}
        </text>
        <line x1="60" y1="60" x2={60 + 26 * Math.sin(((h + m / 60) * Math.PI) / 6)} y2={60 - 26 * Math.cos(((h + m / 60) * Math.PI) / 6)}
          stroke="#2a2118" strokeWidth="4" strokeLinecap="round" />
        <line x1="60" y1="60" x2={60 + 37 * Math.sin(((m + s / 60) * Math.PI) / 30)} y2={60 - 37 * Math.cos(((m + s / 60) * Math.PI) / 30)}
          stroke="#2a2118" strokeWidth="2.6" strokeLinecap="round" />
        <line x1="60" y1="60" x2={60 + 40 * Math.sin((s * Math.PI) / 30)} y2={60 - 40 * Math.cos((s * Math.PI) / 30)}
          stroke="#b3261e" strokeWidth="1.2" strokeLinecap="round" />
        <circle cx="60" cy="60" r="3.2" fill="#b3261e" />
      </svg>
      <div className="clock-plaque">
        <span className="plaque-label">Shop date</span>
        <span className="plaque-date">{pretty}</span>
      </div>
    </div>
  );
}
