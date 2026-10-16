export type AgentId = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  resolved: boolean;
}

export interface ToolCall {
  tool: string;
  args: unknown;
  call_id?: string;
}

export interface AuditEvent {
  ts: string;
  event: string;
  summary: string;
  run_id?: string;
  ticket_id?: number | null;
  agent?: AgentId | null;
  chain?: AgentId[];
  depth?: number;
  step?: number;
  text?: string | null;
  tool_calls?: ToolCall[];
  tool?: string;
  result?: string;
  to_agent?: AgentId;
  task?: string;
  output?: string;
  reason?: string;
  stop_reason?: string;
  detail?: string;
  request?: { ticket_id?: number | null; kind?: string; amount?: number } | null;
}

export interface PaymentRequest {
  id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number | null;
  ticket_id: number | null;
  vendor_id: number | null;
  sku: string | null;
  size: string | null;
  qty: number | null;
  amount: number;
  account: string;
  requested_by: AgentId;
  reason: string | null;
  status: string;
  expected_arrival: string | null;
  created_at: string;
  payee: string | null;
}

export interface Cash {
  account: string;
  balance: number;
  as_of: string;
  pending_total: number;
  available_after_pending: number;
}

export interface RunInfo {
  run_id: string;
  ticket_id: number;
  status: "running" | "finished" | "stopped" | "failed";
  started_at: string;
  finished_at?: string;
  error?: string;
}

export interface Desk {
  shop_date: string;
}
