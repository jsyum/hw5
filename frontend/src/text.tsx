import type { ReactNode } from "react";

/**
 * Render the agents' markdown bold (**text**) as <strong>. Everything else stays plain text.
 * Built from React elements (no HTML injection), so agent text can never inject markup.
 */
export function renderBold(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*/gs;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    out.push(<strong key={k++}>{m[1]}</strong>);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}
