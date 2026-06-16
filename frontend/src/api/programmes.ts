import { api } from "./client";

export type Lesson = {
  id: string;
  module_id: string;
  title: string;
  content_ref: string | null;
  meeting_url: string | null;
  order_index: number;
};

export type LessonWithContent = Lesson & {
  content: Record<string, unknown> | null;
};

export type Module = {
  id: string;
  programme_id: string;
  title: string;
  order_index: number;
  lessons: Lesson[];
};

export type Programme = {
  id: string;
  tenant_id: string | null;
  name: string;
  language: string;
  modules: Module[];
};

export type Curriculum = { programmes: Programme[] };

export type GroupProgramme = { group_id: string; programme_id: string };

export const programmesApi = {
  list: () => api<Programme[]>("/programmes", { method: "GET", auth: true }),
  get: (id: string) =>
    api<Programme>(`/programmes/${id}`, { method: "GET", auth: true }),
  create: (name: string, language: string, tenant_id: string | null) =>
    api<Programme>("/programmes", {
      body: { name, language, tenant_id },
      auth: true,
    }),
  patch: (id: string, payload: { name?: string; language?: string }) =>
    api<Programme>(`/programmes/${id}`, {
      method: "PATCH",
      body: payload,
      auth: true,
    }),
  remove: (id: string) =>
    api<void>(`/programmes/${id}`, { method: "DELETE", auth: true }),

  createModule: (programme_id: string, title: string, order_index: number) =>
    api<Module>(`/programmes/${programme_id}/modules`, {
      body: { title, order_index },
      auth: true,
    }),
};

export const modulesApi = {
  patch: (
    id: string,
    payload: { title?: string; order_index?: number }
  ) =>
    api<Module>(`/modules/${id}`, {
      method: "PATCH",
      body: payload,
      auth: true,
    }),
  remove: (id: string) =>
    api<void>(`/modules/${id}`, { method: "DELETE", auth: true }),
  createLesson: (
    module_id: string,
    title: string,
    content_ref: string | null,
    order_index: number,
    meeting_url: string | null = null
  ) =>
    api<Lesson>(`/modules/${module_id}/lessons`, {
      body: { title, content_ref, order_index, meeting_url },
      auth: true,
    }),
};

export const lessonsApi = {
  get: (id: string) =>
    api<LessonWithContent>(`/lessons/${id}`, { method: "GET", auth: true }),
  patch: (
    id: string,
    payload: {
      title?: string;
      content_ref?: string | null;
      meeting_url?: string | null;
      order_index?: number;
    }
  ) =>
    api<Lesson>(`/lessons/${id}`, {
      method: "PATCH",
      body: payload,
      auth: true,
    }),
  remove: (id: string) =>
    api<void>(`/lessons/${id}`, { method: "DELETE", auth: true }),
};

export const groupProgrammesApi = {
  list: (group_id: string) =>
    api<GroupProgramme[]>(`/groups/${group_id}/programmes`, {
      method: "GET",
      auth: true,
    }),
  assign: (group_id: string, programme_id: string) =>
    api<GroupProgramme>(`/groups/${group_id}/programmes`, {
      body: { programme_id },
      auth: true,
    }),
  unassign: (group_id: string, programme_id: string) =>
    api<void>(`/groups/${group_id}/programmes/${programme_id}`, {
      method: "DELETE",
      auth: true,
    }),
};

export const curriculumApi = {
  me: () =>
    api<Curriculum>("/children/me/curriculum", { method: "GET", auth: true }),
};
