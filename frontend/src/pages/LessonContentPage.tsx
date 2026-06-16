import { useCallback, useEffect, useRef, useState } from "react";
import {
  Body1,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Spinner,
  Textarea,
  Title2,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { cmsApi, type CmsAttachment, type CmsLesson } from "../api/cms";
import { ApiError } from "../api/client";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  hint: {
    color: tokens.colorNeutralForeground2,
    fontSize: "13px",
    marginBottom: "12px",
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("16px"),
    marginBottom: "12px",
  },
  cardHead: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
  },
  meta: {
    color: tokens.colorNeutralForeground2,
    fontSize: "12px",
    marginTop: "4px",
  },
  preview: {
    whiteSpace: "pre-wrap",
    marginTop: "8px",
    color: tokens.colorNeutralForeground1,
    fontSize: "13px",
    maxHeight: "80px",
    overflow: "hidden",
  },
  refLine: {
    fontFamily: "monospace",
    fontSize: "12px",
    color: tokens.colorNeutralForeground3,
    marginTop: "4px",
  },
  actions: { display: "flex", gap: "8px" },
  dialogStack: { display: "flex", flexDirection: "column", gap: "12px" },
  attachRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "8px",
    ...shorthands.padding("8px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorNeutralBackground2,
  },
  attachList: { display: "flex", flexDirection: "column", gap: "6px" },
  attachMeta: { fontSize: "12px", color: tokens.colorNeutralForeground2 },
  hidden: { display: "none" },
});

type EditorState =
  | { mode: "closed" }
  | { mode: "create" }
  | { mode: "edit"; row: CmsLesson };

export default function LessonContentPage() {
  const s = useStyles();
  const [rows, setRows] = useState<CmsLesson[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editor, setEditor] = useState<EditorState>({ mode: "closed" });
  const [toDelete, setToDelete] = useState<CmsLesson | null>(null);

  const reload = useCallback(async () => {
    try {
      setError(null);
      const data = await cmsApi.list();
      setRows(data);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.detail || `HTTP ${e.status}` : String(e)
      );
      setRows([]);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function onDelete() {
    if (!toDelete) return;
    try {
      await cmsApi.remove(toDelete.id);
      setToDelete(null);
      await reload();
    } catch (e) {
      setError(
        e instanceof ApiError ? e.detail || `HTTP ${e.status}` : String(e)
      );
    }
  }

  return (
    <AppShell>
      <div className={s.header}>
        <Title2>{t.cms.title}</Title2>
        <Button
          appearance="primary"
          onClick={() => setEditor({ mode: "create" })}
        >
          {t.cms.createBtn}
        </Button>
      </div>

      <Body1 className={s.hint}>{t.cms.hint}</Body1>

      {error && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}

      {rows === null ? (
        <Spinner label={t.common.loading} />
      ) : rows.length === 0 ? (
        <Body1>{t.cms.empty}</Body1>
      ) : (
        rows.map((r) => (
          <div key={r.id} className={s.card}>
            <div className={s.cardHead}>
              <div style={{ flex: 1 }}>
                <strong>{r.title}</strong>
                <div className={s.meta}>
                  {t.cms.localeLabel}: {r.locale} ·{" "}
                  {t.cms.updatedLabel}:{" "}
                  {new Date(r.updated_at).toLocaleString("ru-RU")}
                  {r.attachments && r.attachments.length > 0 && (
                    <> · {t.cms.attachments}: {r.attachments.length}</>
                  )}
                </div>
                <div className={s.refLine}>
                  content_ref: items/lessons/{r.id}
                </div>
                {r.body && <div className={s.preview}>{r.body}</div>}
              </div>
              <div className={s.actions}>
                <Button onClick={() => setEditor({ mode: "edit", row: r })}>
                  {t.common.edit}
                </Button>
                <Button appearance="subtle" onClick={() => setToDelete(r)}>
                  {t.common.delete}
                </Button>
              </div>
            </div>
          </div>
        ))
      )}

      {editor.mode !== "closed" && (
        <EditorDialog
          state={editor}
          onClose={() => setEditor({ mode: "closed" })}
          onSaved={async () => {
            setEditor({ mode: "closed" });
            await reload();
          }}
        />
      )}

      <ConfirmDialog
        open={toDelete !== null}
        title={t.cms.confirmDeleteTitle}
        body={t.cms.confirmDeleteBody.replace("{0}", toDelete?.title ?? "")}
        onConfirm={onDelete}
        onCancel={() => setToDelete(null)}
      />
    </AppShell>
  );
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function EditorDialog({
  state,
  onClose,
  onSaved,
}: {
  state: Exclude<EditorState, { mode: "closed" }>;
  onClose: () => void;
  onSaved: () => Promise<void> | void;
}) {
  const s = useStyles();
  const editing = state.mode === "edit" ? state.row : null;
  const [title, setTitle] = useState(editing?.title ?? "");
  const [body, setBody] = useState(editing?.body ?? "");
  const [locale, setLocale] = useState(editing?.locale ?? "uk");
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [attachments, setAttachments] = useState<CmsAttachment[]>(
    editing?.attachments ?? []
  );
  const [uploading, setUploading] = useState(false);
  const [toDeleteAtt, setToDeleteAtt] = useState<CmsAttachment | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function onSave() {
    if (!title.trim()) {
      setErr(t.cms.errTitleRequired);
      return;
    }
    setErr(null);
    setSaving(true);
    try {
      if (editing) {
        await cmsApi.update(editing.id, { title, body, locale });
      } else {
        await cmsApi.create({ title, body, locale });
      }
      await onSaved();
    } catch (e) {
      setErr(
        e instanceof ApiError ? e.detail || `HTTP ${e.status}` : String(e)
      );
    } finally {
      setSaving(false);
    }
  }

  async function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f || !editing) return;
    if (f.size > 25 * 1024 * 1024) {
      setErr(t.cms.errFileTooLarge);
      return;
    }
    setErr(null);
    setUploading(true);
    try {
      const att = await cmsApi.uploadAttachment(editing.id, f);
      setAttachments((prev) => [att, ...prev]);
    } catch (ex) {
      setErr(
        ex instanceof ApiError ? ex.detail || `HTTP ${ex.status}` : String(ex)
      );
    } finally {
      setUploading(false);
    }
  }

  async function onConfirmDeleteAtt() {
    if (!editing || !toDeleteAtt) return;
    try {
      await cmsApi.deleteAttachment(editing.id, toDeleteAtt.id);
      setAttachments((prev) => prev.filter((a) => a.id !== toDeleteAtt.id));
      setToDeleteAtt(null);
    } catch (ex) {
      setErr(
        ex instanceof ApiError ? ex.detail || `HTTP ${ex.status}` : String(ex)
      );
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>
            {editing ? t.cms.editTitle : t.cms.createTitle}
          </DialogTitle>
          <DialogContent>
            <div className={s.dialogStack}>
              {err && (
                <MessageBar intent="error">
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <Field label={t.cms.fieldTitle} required>
                <Input
                  value={title}
                  onChange={(_, d) => setTitle(d.value)}
                  maxLength={255}
                />
              </Field>
              <Field label={t.cms.fieldLocale}>
                <Input
                  value={locale}
                  onChange={(_, d) => setLocale(d.value)}
                  maxLength={8}
                />
              </Field>
              <Field label={t.cms.fieldBody}>
                <Textarea
                  value={body}
                  onChange={(_, d) => setBody(d.value)}
                  rows={8}
                  resize="vertical"
                />
              </Field>

              <Field label={t.cms.attachments}>
                <Body1 className={s.attachMeta}>
                  {t.cms.attachmentsHint}
                </Body1>
                {!editing ? (
                  <Body1 className={s.attachMeta}>
                    {t.cms.saveBeforeUpload}
                  </Body1>
                ) : (
                  <>
                    <div style={{ marginTop: 8 }}>
                      <Button
                        appearance="secondary"
                        disabled={uploading}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        {uploading ? t.cms.uploading : t.cms.uploadBtn}
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        className={s.hidden}
                        onChange={onFileChange}
                      />
                    </div>
                    <div className={s.attachList} style={{ marginTop: 8 }}>
                      {attachments.length === 0 ? (
                        <Body1 className={s.attachMeta}>
                          {t.cms.noAttachments}
                        </Body1>
                      ) : (
                        attachments.map((a) => (
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
                            <div className={s.actions}>
                              <Button
                                size="small"
                                onClick={() =>
                                  cmsApi.downloadAttachment(
                                    editing.id,
                                    a.id,
                                    a.file_name
                                  )
                                }
                              >
                                {t.cms.download}
                              </Button>
                              <Button
                                size="small"
                                appearance="subtle"
                                onClick={() => setToDeleteAtt(a)}
                              >
                                {t.common.delete}
                              </Button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </>
                )}
              </Field>

              {editing && (
                <Body1 className={s.refLine}>
                  content_ref: items/lessons/{editing.id}
                </Body1>
              )}
            </div>
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose} disabled={saving}>
              {t.common.cancel}
            </Button>
            <Button
              appearance="primary"
              onClick={onSave}
              disabled={saving}
            >
              {saving ? t.common.loading : t.common.save}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
      <ConfirmDialog
        open={toDeleteAtt !== null}
        title={t.cms.confirmDeleteAttachment}
        body={t.cms.confirmDeleteAttachmentBody.replace(
          "{0}",
          toDeleteAtt?.file_name ?? ""
        )}
        onConfirm={onConfirmDeleteAtt}
        onCancel={() => setToDeleteAtt(null)}
      />
    </Dialog>
  );
}