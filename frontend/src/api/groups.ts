import { api } from "./client";
import type { Child } from "./children";

export type Group = {
  id: string;
  name: string;
  school_id: string;
  teacher_id: string;
};

export type GroupMember = { group_id: string; child_id: string };

export const groupsApi = {
  list: () => api<Group[]>("/groups", { method: "GET", auth: true }),
  create: (school_id: string, teacher_id: string, name: string) =>
    api<Group>("/groups", { body: { school_id, teacher_id, name }, auth: true }),
  patch: (id: string, name: string) =>
    api<Group>(`/groups/${id}`, { method: "PATCH", body: { name }, auth: true }),
  remove: (id: string) =>
    api<void>(`/groups/${id}`, { method: "DELETE", auth: true }),

  listMembers: (group_id: string) =>
    api<Child[]>(`/groups/${group_id}/members`, { method: "GET", auth: true }),
  addMember: (group_id: string, child_id: string) =>
    api<GroupMember>(`/groups/${group_id}/members`, { body: { child_id }, auth: true }),
  removeMember: (group_id: string, child_id: string) =>
    api<void>(`/groups/${group_id}/members/${child_id}`, {
      method: "DELETE",
      auth: true,
    }),
};