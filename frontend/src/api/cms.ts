import { api, ApiError } from "./client";
import { getTokens } from "../auth/tokenStore";

export type CmsAttachment = {
  id: number;
  lesson_id: number;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export type CmsLesson = {
  id: number;
  title: string;
  body: string;
  locale: string;
  created_at: string;
  updated_at: string;
  attachments?: CmsAttachment[];
};

type CmsEnvelope<T> = { data: T };

export type CmsLessonIn = {
  title: string;
  body: string;
  locale: string;
};

export type CmsLessonPatch = Partial<CmsLessonIn>;

const API_BASE = "/api/v1";

function authHeaders(): Record<string, string> {
  const t = getTokens();
  return t?.access_token ? { Authorization: `Bearer ${t.access_token}` } : {};
}

export const cmsApi = {
  list: async (): Promise<CmsLesson[]> => {
    const r = await api<CmsEnvelope<CmsLesson[]>>("/cms/lessons", {
      method: "GET",
      auth: true,
    });
    return r.data;
  },
  get: async (id: number): Promise<CmsLesson> => {
    const r = await api<CmsEnvelope<CmsLesson>>(`/cms/lessons/${id}`, {
      method: "GET",
      auth: true,
    });
    return r.data;
  },
  create: async (payload: CmsLessonIn): Promise<CmsLesson> => {
    const r = await api<CmsEnvelope<CmsLesson>>("/cms/lessons", {
      body: payload,
      auth: true,
    });
    return r.data;
  },
  update: async (id: number, payload: CmsLessonPatch): Promise<CmsLesson> => {
    const r = await api<CmsEnvelope<CmsLesson>>(`/cms/lessons/${id}`, {
      method: "PATCH",
      body: payload,
      auth: true,
    });
    return r.data;
  },
  remove: (id: number) =>
    api<void>(`/cms/lessons/${id}`, { method: "DELETE", auth: true }),

  listAttachments: async (lessonId: number): Promise<CmsAttachment[]> => {
    const r = await api<CmsEnvelope<CmsAttachment[]>>(
      `/cms/lessons/${lessonId}/attachments`,
      { method: "GET", auth: true }
    );
    return r.data;
  },

  uploadAttachment: async (
    lessonId: number,
    file: File
  ): Promise<CmsAttachment> => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(
      `${API_BASE}/cms/lessons/${lessonId}/attachments`,
      {
        method: "POST",
        headers: authHeaders(),
        body: fd,
      }
    );
    if (!res.ok) {
      let detail: string | undefined;
      try {
        const data = await res.json();
        if (typeof data?.detail === "string") detail = data.detail;
      } catch {
        /* ignore */
      }
      throw new ApiError(res.status, detail);
    }
    const env = (await res.json()) as CmsEnvelope<CmsAttachment>;
    return env.data;
  },

  deleteAttachment: (lessonId: number, attId: number) =>
    api<void>(`/cms/lessons/${lessonId}/attachments/${attId}`, {
      method: "DELETE",
      auth: true,
    }),

  attachmentDownloadUrl: (lessonId: number, attId: number) =>
    `${API_BASE}/cms/lessons/${lessonId}/attachments/${attId}`,

  downloadAttachment: async (
    lessonId: number,
    attId: number,
    fileName: string
  ): Promise<void> => {
    const res = await fetch(
      `${API_BASE}/cms/lessons/${lessonId}/attachments/${attId}`,
      { headers: authHeaders() }
    );
    if (!res.ok) throw new ApiError(res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};