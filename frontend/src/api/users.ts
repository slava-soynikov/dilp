import { api } from "./client";

export type Me = {
  id: string;
  email: string | null;
  username: string | null;
  status: string;
  roles: string[];
  created_at: string;
};

export const usersApi = {
  me: () => api<Me>("/users/me", { method: "GET", auth: true }),

  patchMe: (payload: Record<string, unknown>) =>
    api<Me>("/users/me", { method: "PATCH", body: payload, auth: true }),

  deleteMe: () =>
    api<void>("/users/me", { method: "DELETE", auth: true }),

  exportMe: async (): Promise<void> => {
    const tokens = JSON.parse(localStorage.getItem("dilp.tokens") || "null");
    const res = await fetch("/api/v1/users/me/export", {
      headers: tokens?.access_token
        ? { Authorization: `Bearer ${tokens.access_token}` }
        : {},
    });
    if (!res.ok) throw new Error(`Export fehlgeschlagen (${res.status})`);
    const blob = await res.blob();
    const filename =
      res.headers
        .get("content-disposition")
        ?.match(/filename=([^;]+)/)?.[1]
        ?.replace(/^"|"$/g, "") || "dilp-export.json";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};