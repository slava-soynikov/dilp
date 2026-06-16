import { api } from "./client";

export type Child = {
  id: string;
  user_id: string | null;
  username: string | null;
  status: string | null;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  native_language: string | null;
  school_id: string | null;
};

export type ChildCreateInput = {
  username: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  native_language?: string;
};

export type ChildCreateResponse = Child & { pin: string };

export type ChildPatchInput = Partial<{
  first_name: string;
  last_name: string;
  date_of_birth: string;
  native_language: string;
}>;

export const childrenApi = {
  list: () => api<Child[]>("/children", { method: "GET", auth: true }),

  create: (payload: ChildCreateInput) =>
    api<ChildCreateResponse>("/children", { body: payload, auth: true }),

  patch: (id: string, payload: ChildPatchInput) =>
    api<Child>(`/children/${id}`, { method: "PATCH", body: payload, auth: true }),
};