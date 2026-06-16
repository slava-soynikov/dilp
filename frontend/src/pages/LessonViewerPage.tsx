import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Body1,
  Button,
  MessageBar,
  MessageBarBody,
  Spinner,
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import ReactMarkdown from "react-markdown";
import { AppShell } from "../components/AppShell";
import { lessonsApi, type LessonWithContent } from "../api/programmes";
import { cmsApi, type CmsAttachment } from "../api/cms";
import { ApiError } from "../api/client";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  head: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("20px"),
    marginTop: "12px",
  },
  meta: { color: tokens.colorNeutralForeground2, fontSize: "12px" },
  pre: {
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.padding("12px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: "12px",
    overflowX: "auto",
  },
  attachRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "8px",
    ...shorthands.padding("8px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorNeutralBackground2,
    marginTop: "6px",
  },
  attachMeta: { fontSize: "12px", color: tokens.colorNeutralForeground2 },
});

/**
 * Extracts a renderable "body" from a CMS response envelope.
 * Supports two shapes:
 *   { data: { body|content|markdown, title? } }          (DILP mini-CMS / Directus)
 *   { data: { attributes: { body|content|markdown } } }  (Strapi)
 * Falls back to raw JSON for unknown shapes.
 */
function extractRenderable(content: Record<string, unknown> | null): {
  title?: string;
  body?: string;
  attachments: CmsAttachment[];
  lessonId?: number;
  raw: unknown;
} {
  if (!content) return { attachments: [], raw: null };
  const data = (content as any).data;
  const attrs =
    (data && typeof data === "object" && (data as any).attributes) || null;
  const src =
    attrs || (data && typeof data === "object" ? data : null) || content;
  const title =
    typeof (src as any)?.title === "string"
      ? ((src as any).title as string)
      : undefined;
  const body =
    typeof (src as any)?.body === "string"
      ? ((src as any).body as string)
      : typeof (src as any)?.content === "string"
      ? ((src as any).content as string)
      : typeof (src as any)?.markdown === "string"
      ? ((src as any).markdown as string)
      : undefined;
  const attachments: CmsAttachment[] = Array.isArray((src as any)?.attachments)
    ? ((src as any).attachments as CmsAttachment[])
    : [];
  const lessonId =
    typeof (src as any)?.id === "number" ? ((src as any).id as number) : undefined;
  return { title, body, attachments, lessonId, raw: content };
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function LessonViewerPage() {
  const s = useStyles();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<LessonWithContent | null>(null);
  const [err, setErr] = useState<string>();
  const [cmsErr, setCmsErr] = useState<string>();

  const load = useCallback(async () => {
    if (!id) return;
    setErr(undefined);
    setCmsErr(undefined);
    try {
      const l = await lessonsApi.get(id);
      setLesson(l);
    } catch (e) {
      if (e instanceof ApiError && e.status === 502) setCmsErr(t.lesson.cmsError);
      else if (e instanceof ApiError && e.status === 404)
        setErr(t.common.error);
      else setErr(t.common.networkError);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const renderable = extractRenderable(lesson?.content || null);

  return (
    <AppShell>
      <div className={s.head}>
        <Title2>{lesson?.title || t.lesson.title}</Title2>
        <Button onClick={() => navigate(-1)}>{t.lesson.back}</Button>
      </div>

      {err && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}
      {cmsErr && (
        <MessageBar intent="warning" style={{ marginBottom: 12 }}>
          <MessageBarBody>{cmsErr}</MessageBarBody>
        </MessageBar>
      )}

      {!lesson && !err && !cmsErr ? (
        <Spinner label={t.common.loading} />
      ) : lesson ? (
        <>
          <div className={s.card}>
            <div className={s.meta}>
              {lesson.content_ref || t.lesson.noContent}
            </div>
            {lesson.meeting_url && (
              <div style={{ marginTop: 12 }}>
                <Button
                  appearance="primary"
                  as="a"
                  href={lesson.meeting_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t.lesson.joinMeeting}
                </Button>
              </div>
            )}
          </div>
          {lesson.content && (
            <div className={s.card}>
              <Title3>{renderable.title || t.lesson.contentTitle}</Title3>
              {renderable.body ? (
                <ReactMarkdown>{renderable.body}</ReactMarkdown>
              ) : !renderable.attachments.length ? (
                <>
                  <Body1>{t.lesson.rawTitle}</Body1>
                  <pre className={s.pre}>
                    {JSON.stringify(renderable.raw, null, 2)}
                  </pre>
                </>
              ) : null}
            </div>
          )}
          {renderable.attachments.length > 0 && renderable.lessonId != null && (
            <div className={s.card}>
              <Title3>{t.lesson.attachmentsTitle}</Title3>
              {renderable.attachments.map((a) => (
                <div key={a.id} className={s.attachRow}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {a.file_name}
                    </div>
                    <div className={s.attachMeta}>
                      {a.mime_type} · {formatBytes(a.size_bytes)}
                    </div>
                  </div>
                  <Button
                    size="small"
                    onClick={() =>
                      cmsApi.downloadAttachment(
                        renderable.lessonId as number,
                        a.id,
                        a.file_name
                      )
                    }
                  >
                    {t.lesson.download}
                  </Button>
                </div>
              ))}
            </div>
          )}
          {!lesson.content && !cmsErr && (
            <Body1>{t.lesson.noContent}</Body1>
          )}
        </>
      ) : null}
    </AppShell>
  );
}
