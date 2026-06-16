import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Body1,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Dropdown,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Option,
  Spinner,
  SpinButton,
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import {
  modulesApi,
  programmesApi,
  lessonsApi,
  type Lesson,
  type Module,
  type Programme,
} from "../api/programmes";
import { tenantsApi, type Tenant } from "../api/tenants";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
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
  },
  meta: { color: tokens.colorNeutralForeground2, fontSize: "12px" },
  actions: { display: "flex", gap: "8px" },
  moduleBlock: {
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.padding("12px"),
    marginTop: "8px",
  },
  moduleHead: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  lessonRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.padding("6px", "8px"),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    backgroundColor: tokens.colorNeutralBackground1,
    marginTop: "6px",
  },
  formCol: { display: "flex", flexDirection: "column", gap: "12px" },
});

export default function ProgrammesPage() {
  const s = useStyles();
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");

  const [programmes, setProgrammes] = useState<Programme[] | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [err, setErr] = useState<string>();
  const [openCreate, setOpenCreate] = useState(false);
  const [editP, setEditP] = useState<Programme | null>(null);
  const [deleteP, setDeleteP] = useState<Programme | null>(null);
  const [busy, setBusy] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const [ps, ts] = await Promise.all([
        programmesApi.list(),
        isAdmin
          ? tenantsApi.list().catch(() => [] as Tenant[])
          : Promise.resolve([] as Tenant[]),
      ]);
      setProgrammes(ps);
      setTenants(ts);
    } catch {
      setErr(t.common.networkError);
    }
  }, [isAdmin]);

  useEffect(() => {
    load();
  }, [load]);

  const tenantsById = useMemo(
    () => Object.fromEntries(tenants.map((x) => [x.id, x])),
    [tenants]
  );

  return (
    <AppShell>
      <div className={s.header}>
        <Title2>
          {isAdmin ? t.programmes.title : t.programmes.titleTeacher}
        </Title2>
        {isAdmin && (
          <Button appearance="primary" onClick={() => setOpenCreate(true)}>
            {t.programmes.add}
          </Button>
        )}
      </div>

      {err && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {programmes === null ? (
        <Spinner label={t.common.loading} />
      ) : programmes.length === 0 ? (
        <Body1>{t.programmes.empty}</Body1>
      ) : (
        programmes.map((p) => (
          <div key={p.id} className={s.card}>
            <div className={s.cardHead}>
              <div>
                <div style={{ fontWeight: 600 }}>{p.name}</div>
                <div className={s.meta}>
                  {p.language} ·{" "}
                  {p.tenant_id
                    ? tenantsById[p.tenant_id]?.name || p.tenant_id
                    : t.programmes.global}{" "}
                  · {p.id}
                </div>
              </div>
              <div className={s.actions}>
                <Button
                  onClick={() =>
                    setExpanded((m) => ({ ...m, [p.id]: !m[p.id] }))
                  }
                >
                  {expanded[p.id]
                    ? t.programmes.close
                    : t.programmes.open}
                </Button>
                {isAdmin && (
                  <>
                    <Button onClick={() => setEditP(p)}>
                      {t.common.edit}
                    </Button>
                    <Button onClick={() => setDeleteP(p)}>
                      {t.common.delete}
                    </Button>
                  </>
                )}
              </div>
            </div>
            {expanded[p.id] && (
              <ModulesSection programme={p} onChanged={load} />
            )}
          </div>
        ))
      )}

      {openCreate && (
        <ProgrammeFormDialog
          tenants={tenants}
          onClose={() => setOpenCreate(false)}
          onDone={() => {
            setOpenCreate(false);
            load();
          }}
        />
      )}

      {editP && (
        <ProgrammeFormDialog
          tenants={tenants}
          programme={editP}
          onClose={() => setEditP(null)}
          onDone={() => {
            setEditP(null);
            load();
          }}
        />
      )}

      <ConfirmDialog
        open={deleteP !== null}
        title={t.programmes.confirmDelete}
        body={t.programmes.confirmDeleteBody}
        destructive
        busy={busy}
        onConfirm={async () => {
          if (!deleteP) return;
          setBusy(true);
          try {
            await programmesApi.remove(deleteP.id);
          } finally {
            setBusy(false);
            setDeleteP(null);
            load();
          }
        }}
        onCancel={() => setDeleteP(null)}
      />
    </AppShell>
  );
}

function ProgrammeFormDialog({
  tenants,
  programme,
  onClose,
  onDone,
}: {
  tenants: Tenant[];
  programme?: Programme;
  onClose: () => void;
  onDone: () => void;
}) {
  const isEdit = !!programme;
  const [name, setName] = useState(programme?.name || "");
  const [language, setLanguage] = useState(programme?.language || "uk");
  const [tenantId, setTenantId] = useState<string>(programme?.tenant_id || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !language.trim()) return;
    setBusy(true);
    setErr(undefined);
    try {
      if (isEdit && programme) {
        await programmesApi.patch(programme.id, {
          name: name.trim(),
          language: language.trim(),
        });
      } else {
        await programmesApi.create(
          name.trim(),
          language.trim(),
          tenantId || null
        );
      }
      onDone();
    } catch (e) {
      if (e instanceof ApiError && e.status === 404)
        setErr(e.detail || t.common.error);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <form onSubmit={submit}>
          <DialogBody>
            <DialogTitle>
              {isEdit ? t.programmes.edit.title : t.programmes.create.title}
            </DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label={t.programmes.name} required>
                  <Input value={name} onChange={(_, d) => setName(d.value)} />
                </Field>
                <Field label={t.programmes.language} required>
                  <Input
                    value={language}
                    onChange={(_, d) => setLanguage(d.value)}
                  />
                </Field>
                {!isEdit && (
                  <Field label={t.programmes.tenant}>
                    <Dropdown
                      value={
                        tenantId
                          ? tenants.find((x) => x.id === tenantId)?.name ||
                            tenantId
                          : t.programmes.tenantNone
                      }
                      selectedOptions={[tenantId]}
                      onOptionSelect={(_, d) =>
                        setTenantId(String(d.optionValue || ""))
                      }
                    >
                      <Option value="" text={t.programmes.tenantNone}>
                        {t.programmes.tenantNone}
                      </Option>
                      {tenants.map((tn) => (
                        <Option key={tn.id} value={tn.id} text={tn.name}>
                          {tn.name}
                        </Option>
                      ))}
                    </Dropdown>
                  </Field>
                )}
              </div>
            </DialogContent>
            <DialogActions>
              <Button type="button" onClick={onClose} disabled={busy}>
                {t.common.cancel}
              </Button>
              <Button appearance="primary" type="submit" disabled={busy}>
                {busy
                  ? t.common.loading
                  : isEdit
                  ? t.programmes.edit.submit
                  : t.programmes.create.submit}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  );
}

function ModulesSection({
  programme,
  onChanged,
}: {
  programme: Programme;
  onChanged: () => void;
}) {
  const s = useStyles();
  const navigate = useNavigate();
  const [data, setData] = useState<Programme>(programme);
  const [err, setErr] = useState<string>();
  const [openAdd, setOpenAdd] = useState(false);
  const [editM, setEditM] = useState<Module | null>(null);
  const [delM, setDelM] = useState<Module | null>(null);
  const [busy, setBusy] = useState(false);

  // Lessons
  const [openLesson, setOpenLesson] = useState<{
    module: Module;
    lesson?: Lesson;
  } | null>(null);
  const [delLesson, setDelLesson] = useState<Lesson | null>(null);

  const reload = useCallback(async () => {
    try {
      const fresh = await programmesApi.get(programme.id);
      setData(fresh);
      onChanged();
    } catch {
      setErr(t.common.networkError);
    }
  }, [programme.id, onChanged]);

  useEffect(() => {
    setData(programme);
  }, [programme]);

  return (
    <div style={{ marginTop: 12 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Title3>{t.programmes.modules.title}</Title3>
        <Button onClick={() => setOpenAdd(true)}>
          {t.programmes.modules.add}
        </Button>
      </div>

      {err && (
        <MessageBar intent="error" style={{ marginTop: 8 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {data.modules.length === 0 ? (
        <Body1 style={{ marginTop: 8 }}>{t.programmes.modules.empty}</Body1>
      ) : (
        data.modules
          .slice()
          .sort((a, b) => a.order_index - b.order_index)
          .map((m) => (
            <div key={m.id} className={s.moduleBlock}>
              <div className={s.moduleHead}>
                <div>
                  <div style={{ fontWeight: 600 }}>
                    #{m.order_index} · {m.title}
                  </div>
                  <div className={s.meta}>{m.id}</div>
                </div>
                <div className={s.actions}>
                  <Button
                    onClick={() => setOpenLesson({ module: m })}
                  >
                    {t.programmes.lessons.add}
                  </Button>
                  <Button onClick={() => setEditM(m)}>
                    {t.programmes.modules.edit}
                  </Button>
                  <Button onClick={() => setDelM(m)}>
                    {t.common.delete}
                  </Button>
                </div>
              </div>

              {m.lessons.length === 0 ? (
                <Body1 style={{ marginTop: 6 }}>
                  {t.programmes.lessons.empty}
                </Body1>
              ) : (
                m.lessons
                  .slice()
                  .sort((a, b) => a.order_index - b.order_index)
                  .map((l) => (
                    <div key={l.id} className={s.lessonRow}>
                      <div>
                        <div>
                          #{l.order_index} · {l.title}
                        </div>
                        <div className={s.meta}>
                          {l.content_ref || t.common.none}
                        </div>
                      </div>
                      <div className={s.actions}>
                        <Button
                          onClick={() => navigate(`/lessons/${l.id}`)}
                        >
                          {t.programmes.lessons.open}
                        </Button>
                        <Button
                          onClick={() =>
                            setOpenLesson({ module: m, lesson: l })
                          }
                        >
                          {t.programmes.lessons.edit}
                        </Button>
                        <Button onClick={() => setDelLesson(l)}>
                          {t.common.delete}
                        </Button>
                      </div>
                    </div>
                  ))
              )}
            </div>
          ))
      )}

      {openAdd && (
        <ModuleFormDialog
          programmeId={data.id}
          onClose={() => setOpenAdd(false)}
          onDone={() => {
            setOpenAdd(false);
            reload();
          }}
        />
      )}

      {editM && (
        <ModuleFormDialog
          programmeId={data.id}
          module={editM}
          onClose={() => setEditM(null)}
          onDone={() => {
            setEditM(null);
            reload();
          }}
        />
      )}

      <ConfirmDialog
        open={delM !== null}
        title={t.programmes.modules.confirmDelete}
        body={t.programmes.modules.confirmDeleteBody}
        destructive
        busy={busy}
        onConfirm={async () => {
          if (!delM) return;
          setBusy(true);
          try {
            await modulesApi.remove(delM.id);
          } catch (e) {
            if (e instanceof ApiError && e.status === 403)
              setErr(t.programmes.modules.forbidden);
            else setErr(t.common.networkError);
          } finally {
            setBusy(false);
            setDelM(null);
            reload();
          }
        }}
        onCancel={() => setDelM(null)}
      />

      {openLesson && (
        <LessonFormDialog
          module={openLesson.module}
          lesson={openLesson.lesson}
          onClose={() => setOpenLesson(null)}
          onDone={() => {
            setOpenLesson(null);
            reload();
          }}
        />
      )}

      <ConfirmDialog
        open={delLesson !== null}
        title={t.programmes.lessons.confirmDelete}
        body={t.programmes.lessons.confirmDeleteBody}
        destructive
        busy={busy}
        onConfirm={async () => {
          if (!delLesson) return;
          setBusy(true);
          try {
            await lessonsApi.remove(delLesson.id);
          } catch (e) {
            if (e instanceof ApiError && e.status === 403)
              setErr(t.programmes.modules.forbidden);
            else setErr(t.common.networkError);
          } finally {
            setBusy(false);
            setDelLesson(null);
            reload();
          }
        }}
        onCancel={() => setDelLesson(null)}
      />
    </div>
  );
}

function ModuleFormDialog({
  programmeId,
  module,
  onClose,
  onDone,
}: {
  programmeId: string;
  module?: Module;
  onClose: () => void;
  onDone: () => void;
}) {
  const isEdit = !!module;
  const [title, setTitle] = useState(module?.title || "");
  const [order, setOrder] = useState<number>(module?.order_index ?? 0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    setErr(undefined);
    try {
      if (isEdit && module) {
        await modulesApi.patch(module.id, {
          title: title.trim(),
          order_index: order,
        });
      } else {
        await programmesApi.createModule(programmeId, title.trim(), order);
      }
      onDone();
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) setErr(t.programmes.modules.orderConflict);
        else if (e.status === 403) setErr(t.programmes.modules.forbidden);
        else setErr(e.detail || t.common.error);
      } else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <form onSubmit={submit}>
          <DialogBody>
            <DialogTitle>
              {isEdit ? t.programmes.modules.edit : t.programmes.modules.add}
            </DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label={t.programmes.modules.moduleTitle} required>
                  <Input value={title} onChange={(_, d) => setTitle(d.value)} />
                </Field>
                <Field label={t.programmes.modules.order} required>
                  <SpinButton
                    value={order}
                    onChange={(_, d) => {
                      if (typeof d.value === "number") setOrder(d.value);
                      else if (d.displayValue !== undefined) {
                        const n = parseInt(d.displayValue, 10);
                        if (!isNaN(n)) setOrder(n);
                      }
                    }}
                    min={0}
                  />
                </Field>
              </div>
            </DialogContent>
            <DialogActions>
              <Button type="button" onClick={onClose} disabled={busy}>
                {t.common.cancel}
              </Button>
              <Button appearance="primary" type="submit" disabled={busy}>
                {busy ? t.common.loading : t.common.save}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  );
}

function LessonFormDialog({
  module,
  lesson,
  onClose,
  onDone,
}: {
  module: Module;
  lesson?: Lesson;
  onClose: () => void;
  onDone: () => void;
}) {
  const isEdit = !!lesson;
  const [title, setTitle] = useState(lesson?.title || "");
  const [contentRef, setContentRef] = useState(lesson?.content_ref || "");
  const [meetingUrl, setMeetingUrl] = useState(lesson?.meeting_url || "");
  const [order, setOrder] = useState<number>(lesson?.order_index ?? 0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    setErr(undefined);
    const ref = contentRef.trim() ? contentRef.trim() : null;
    const meet = meetingUrl.trim() ? meetingUrl.trim() : null;
    try {
      if (isEdit && lesson) {
        await lessonsApi.patch(lesson.id, {
          title: title.trim(),
          content_ref: ref,
          meeting_url: meet,
          order_index: order,
        });
      } else {
        await modulesApi.createLesson(module.id, title.trim(), ref, order, meet);
      }
      onDone();
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) setErr(t.programmes.lessons.orderConflict);
        else if (e.status === 403) setErr(t.programmes.modules.forbidden);
        else setErr(e.detail || t.common.error);
      } else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <form onSubmit={submit}>
          <DialogBody>
            <DialogTitle>
              {isEdit ? t.programmes.lessons.edit : t.programmes.lessons.add}
            </DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label={t.programmes.lessons.lessonTitle} required>
                  <Input value={title} onChange={(_, d) => setTitle(d.value)} />
                </Field>
                <Field
                  label={t.programmes.lessons.contentRef}
                  hint={t.programmes.lessons.contentRefHelp}
                >
                  <Input
                    value={contentRef}
                    onChange={(_, d) => setContentRef(d.value)}
                  />
                </Field>
                <Field
                  label={t.programmes.lessons.meetingUrl}
                  hint={t.programmes.lessons.meetingUrlHelp}
                >
                  <Input
                    type="url"
                    value={meetingUrl}
                    placeholder="https://meet.google.com/..."
                    onChange={(_, d) => setMeetingUrl(d.value)}
                  />
                </Field>
                <Field label={t.programmes.lessons.order} required>
                  <SpinButton
                    value={order}
                    onChange={(_, d) => {
                      if (typeof d.value === "number") setOrder(d.value);
                      else if (d.displayValue !== undefined) {
                        const n = parseInt(d.displayValue, 10);
                        if (!isNaN(n)) setOrder(n);
                      }
                    }}
                    min={0}
                  />
                </Field>
              </div>
            </DialogContent>
            <DialogActions>
              <Button type="button" onClick={onClose} disabled={busy}>
                {t.common.cancel}
              </Button>
              <Button appearance="primary" type="submit" disabled={busy}>
                {busy ? t.common.loading : t.common.save}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  );
}
