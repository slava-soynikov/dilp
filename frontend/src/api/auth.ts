import { api } from "./client";
import type { Tokens } from "../auth/tokenStore";

export type UserRead = {
  id: string;
  email: string;
  status: string;
  created_at: string;
};

export const authApi = {
  register: (email: string, password: string, role = "parent") =>
    api<UserRead>("/auth/register", { body: { email, password, role } }),

  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return api<Tokens>("/auth/login", { form });
  },

  refresh: (refresh_token: string) =>
    api<Tokens>("/auth/refresh", { body: { refresh_token } }),

  logout: (refresh_token: string) =>
    api<void>("/auth/logout", { body: { refresh_token } }),

  verifyEmail: (token: string) =>
    api<{ status: string }>("/auth/verify-email", { body: { token } }),

  forgotPassword: (email: string) =>
    api<{ status: string }>("/auth/forgot-password", { body: { email } }),

  resetPassword: (token: string, new_password: string) =>
    api<{ status: string }>("/auth/reset-password", {
      body: { token, new_password },
    }),
};