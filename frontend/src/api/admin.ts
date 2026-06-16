import { api } from "./client";
import type { UserRead } from "./auth";

export type TeacherInviteResult = UserRead & { temp_password: string };

export type ResetPasswordResult = {
  user_id: string;
  email: string | null;
  username: string | null;
  new_password: string;
};

export type TeacherListItem = {
  id: string; // teacher_profile.id — used as group.teacher_id
  user_id: string;
  email: string | null;
  first_name: string;
  last_name: string;
};

export const adminApi = {
  inviteTeacher: (email: string, first_name: string, last_name: string) =>
    api<TeacherInviteResult>("/admin/teachers", {
      body: { email, first_name, last_name },
      auth: true,
    }),
  resetUserPassword: (identifier: string) =>
    api<ResetPasswordResult>("/admin/users/reset-password", {
      body: { identifier },
      auth: true,
    }),
  listTeachers: (q?: string) => {
    const qs = q && q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
    return api<TeacherListItem[]>(`/admin/teachers${qs}`, {
      method: "GET",
      auth: true,
    });
  },
};