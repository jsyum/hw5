import type { AuditEvent, Cash, Desk, PaymentRequest, RunInfo, Ticket } from "./types";

export const API_BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    const msg = typeof detail === "string" ? detail
      : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join("; ")
      : `Request failed (${res.status})`;
    throw new ApiError(res.status, msg);
  }
  return body as T;
}

export const api = {
  tickets: () => call<Ticket[]>("/tickets"),
  events: (ticketId: number) => call<AuditEvent[]>(`/events?ticket_id=${ticketId}&limit=1500`),
  runs: () => call<RunInfo[]>("/runs"),
  run: (runId: string) => call<RunInfo>(`/runs/${runId}`),
  startRun: (ticketId: number) => call<RunInfo>(`/tickets/${ticketId}/run`, { method: "POST" }),
  pending: () => call<PaymentRequest[]>("/payments/pending"),
  approve: (requestId: number, approverName: string) =>
    call<{ status: string; new_balance: number }>(`/payments/${requestId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approver_name: approverName, human_confirmed: true }),
    }),
  cash: () => call<Cash>("/cash"),
  desk: () => call<Desk>("/desk"),
  reset: () => call<{ reset: boolean }>("/reset", { method: "POST" }),
};
