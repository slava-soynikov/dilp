import { api } from "./client";

export type Consent = {
  id: string;
  parent_id: string;
  child_id: string;
  consent_type: string;
  consent_version: string;
  consent_text_ref: string | null;
  granted_at: string;
  revoked_at: string | null;
};

export const consentsApi = {
  list: () => api<Consent[]>("/consents", { method: "GET", auth: true }),

  grant: (child_id: string, consent_type = "data_processing") =>
    api<Consent>("/consents", { body: { child_id, consent_type }, auth: true }),

  revoke: (consent_id: string) =>
    api<Consent>(`/consents/${consent_id}/revoke`, {
      method: "POST",
      auth: true,
    }),
};