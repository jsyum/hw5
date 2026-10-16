import { useCallback, useEffect, useRef, useState } from "react";

/** Polls `fn` every `intervalMs` (null pauses). Returns data, error, and a manual refresh. */
export function usePolling<T>(fn: () => Promise<T>, intervalMs: number | null, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const refresh = useCallback(async () => {
    try {
      const d = await fnRef.current();
      setData(d);
      setError(null);
      return d;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    }
  }, []);

  useEffect(() => {
    let alive = true;
    void refresh();
    if (intervalMs === null) return;
    const id = window.setInterval(() => { if (alive) void refresh(); }, intervalMs);
    return () => { alive = false; window.clearInterval(id); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, refresh, ...deps]);

  return { data, error, refresh, setData };
}
