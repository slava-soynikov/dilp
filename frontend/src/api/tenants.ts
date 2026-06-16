import { api } from "./client";

export type Tenant = { id: string; name: string };
export type School = { id: string; tenant_id: string; name: string };

export const tenantsApi = {
  list: () => api<Tenant[]>("/tenants", { method: "GET", auth: true }),
  create: (name: string) =>
    api<Tenant>("/tenants", { body: { name }, auth: true }),
  patch: (id: string, name: string) =>
    api<Tenant>(`/tenants/${id}`, { method: "PATCH", body: { name }, auth: true }),
  remove: (id: string) =>
    api<void>(`/tenants/${id}`, { method: "DELETE", auth: true }),
};

export const schoolsApi = {
  list: () => api<School[]>("/schools", { method: "GET", auth: true }),
  create: (tenant_id: string, name: string) =>
    api<School>("/schools", { body: { tenant_id, name }, auth: true }),
  patch: (id: string, name: string) =>
    api<School>(`/schools/${id}`, { method: "PATCH", body: { name }, auth: true }),
  remove: (id: string) =>
    api<void>(`/schools/${id}`, { method: "DELETE", auth: true }),
};