import type { AgentId } from "./types";

export interface AgentMeta {
  id: AgentId;
  name: string;
  role: string;
  initials: string;
  /** Sticky-note paper color (always paired with dark ink for contrast). */
  paper: string;
  /** Saturated accent for borders, chair head, chips. */
  accent: string;
  /** Dark ink that reads on the paper color. */
  ink: string;
}

export const AGENTS: AgentMeta[] = [
  { id: "boss", name: "Boss", role: "Assigns work and makes the final call", initials: "BO",
    paper: "#FFE873", accent: "#C99A00", ink: "#3D3000" },
  { id: "inventory", name: "Inventory", role: "Stock, shortages, restock vendors", initials: "IN",
    paper: "#BDF2CF", accent: "#23935C", ink: "#0B3A22" },
  { id: "accounting", name: "Accounting", role: "Cash, invoices, margins, payment requests", initials: "AC",
    paper: "#C3E1FF", accent: "#2F78C4", ink: "#0B2E52" },
  { id: "facilities", name: "Facilities", role: "Leases and rent", initials: "FA",
    paper: "#FFD5AE", accent: "#D46A1A", ink: "#4A2304" },
  { id: "customer_service", name: "Customer Service", role: "Drafts customer messages", initials: "CS",
    paper: "#FFC9E2", accent: "#C93A82", ink: "#4D0C2C" },
];

export const AGENT: Record<AgentId, AgentMeta> = Object.fromEntries(AGENTS.map((a) => [a.id, a])) as Record<AgentId, AgentMeta>;

export function agentName(id: string | null | undefined): string {
  return id && id in AGENT ? AGENT[id as AgentId].name : id ?? "System";
}

export function toolLabel(tool: string): string {
  return tool.replace(/_/g, " ");
}
