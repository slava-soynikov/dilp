import { api } from "./client";

export type ActivityLog = {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
};

export type AuditLog = {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  diff: string | null;
  timestamp: string;
};

export type LogQuery = {
  user_id?: string;
  action?: string;
  entity_type?: string;
  entity_id?: string;
  limit?: number;
  offset?: number;
};

function qs(params: LogQuery): string {
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === "" || v === null) continue;
    usp.append(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

export const logsApi = {
  activity: (params: LogQuery = {}) =>
    api<ActivityLog[]>(`/logs/activity${qs(params)}`, {
      method: "GET",
      auth: true,
    }),

  audit: (params: LogQuery = {}) =>
    api<AuditLog[]>(`/logs/audit${qs(params)}`, {
      method: "GET",
      auth: true,
    }),
};