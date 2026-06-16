import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Body1,
  Button,
  Combobox,
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
  Title2,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { groupsApi, type Group } from "../api/groups";
import { schoolsApi, type School } from "../api/tenants";
import { adminApi, type TeacherListItem } from "../api/admin";
import { type Child } from "../api/children";
import {
  groupProgrammesApi,
  programmesApi,
  type Programme,
} from "../api/programmes";
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
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  meta: { color: tokens.colorNeutralForeground2, fontSize: "12px" },
  actions: { display: "flex", gap: "8px" },
  membersList: { display: "flex", flexDirection: "column", rowGap: "8px" },
  memberRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.padding("8px", "12px"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
});

export default function GroupsPage() {
  const s = useStyles();
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const isTeacher = hasRole("teacher");
  const isParent = hasRole("parent");

  const [groups, setGroups] = useState<Group[] | null>(null);
  const [schools, setSchools] = useState<School[]>([]);
  const [err, setErr] = useState<string>();
  const [openCreate, setOpenCreate] = useState(false);
  const [deleteG, setDeleteG] = useState<Group | null>(null);
  const [manage, setManage] = useState<Group | null>(null);
  const [managePr, setManagePr] = useState<Group | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const [gs, ss] = await Promise.all([
        groupsApi.list(),
        schoolsApi.list().catch(() => [] as School[]),
      ]);
      setGroups(gs);
      setSchools(ss);
    } catch {
      setErr(t.common.networkError);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const schoolsById = useMemo(
    () => Object.fromEntries(schools.map((x) => [x.id, x])),
    [schools]
  );

  const pageTitle = isAdmin
    ? t.groups.title
    : isTeacher
    ? t.groups.titleTeacher
    : isParent
    ? t.groups.titleParent
    : t.groups.title;

  return (
    <AppShell>
      <div className={s.header}>
        <Title2>{pageTitle}</Title2>
        {isAdmin && schools.length > 0 && (
          <Button appearance="primary" onClick={() => setOpenCreate(true)}>
            {t.groups.addGroup}
          </Button>
        )}
      </div>

      {err && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {groups === null ? (
        <Spinner label={t.common.loading} />
      ) : groups.length === 0 ? (
        <Body1>{t.groups.empty}</Body1>
      ) : (
        groups.map((g) => (
          <div key={g.id} className={s.card}>
            <div>
              <div style={{ fontWeight: 600 }}>{g.name}</div>
              <div className={s.meta}>
                {t.groups.school}:{" "}
                {schoolsById[g.school_id]?.name || g.school_id} · {g.id}
              </div>
            </div>
            <div className={s.actions}>
              {(isTeacher || isAdmin) && (
                <Button onClick={() => setManage(g)}>{t.groups.membersBtn}</Button>
              )}
              {(isTeacher || isAdmin) && (
                <Button onClick={() => setManagePr(g)}>
                  {t.groupProgrammes.btn}
                </Button>
              )}
              {isAdmin && (
                <Button onClick={() => setDeleteG(g)}>{t.groups.delete}</Button>
              )}
            </div>
          </div>
        ))
      )}

      {openCreate && (
        <CreateGroupDialog
          schools={schools}
          onClose={() => setOpenCreate(false)}
          onDone={() => {
            setOpenCreate(false);
            load();
          }}
        />
      )}

      {manage && (
        <ManageMembersDialog
          group={manage}
          onClose={() => setManage(null)}
        />
      )}

      {managePr && (
        <ManageProgrammesDialog
          group={managePr}
          onClose={() => setManagePr(null)}
        />
      )}

      <ConfirmDialog
        open={deleteG !== null}
        title={t.groups.confirmDelete}
        body={t.groups.confirmDeleteBody}
        destructive
        busy={busy}
        onConfirm={async () => {
          if (!deleteG) return;
          setBusy(true);
          try {
            await groupsApi.remove(deleteG.id);
          } finally {
            setBusy(false);
            setDeleteG(null);
            load();
          }
        }}
        onCancel={() => setDeleteG(null)}
      />
    </AppShell>
  );
}

function CreateGroupDialog({
  schools,
  onClose,
  onDone,
}: {
  schools: School[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [schoolId, setSchoolId] = useState(schools[0]?.id || "");
  const [teacherId, setTeacherId] = useState("");
  const [teacherQuery, setTeacherQuery] = useState("");
  const [teachers, setTeachers] = useState<TeacherListItem[] | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  useEffect(() => {
    let aborted = false;
    adminApi
      .listTeachers()
      .then((list) => {
        if (!aborted) setTeachers(list);
      })
      .catch(() => {
        if (!aborted) setTeachers([]);
      });
    return () => {
      aborted = true;
    };
  }, []);

  const teacherLabel = (tt: TeacherListItem) =>
    `${tt.last_name}, ${tt.first_name}${tt.email ? ` · ${tt.email}` : ""}`;

  const filteredTeachers = useMemo(() => {
    const list = teachers || [];
    const q = teacherQuery.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (tt) =>
        tt.last_name.toLowerCase().includes(q) ||
        tt.first_name.toLowerCase().includes(q) ||
        (tt.email || "").toLowerCase().includes(q)
    );
  }, [teachers, teacherQuery]);

  const selectedTeacher = useMemo(
    () => (teachers || []).find((tt) => tt.id === teacherId) || null,
    [teachers, teacherId]
  );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!schoolId || !teacherId || !name.trim()) return;
    setBusy(true);
    try {
      await groupsApi.create(schoolId, teacherId, name.trim());
      onDone();
    } catch (e) {
      if (e instanceof ApiError && e.status === 404)
        setErr(t.groups.members.notFound);
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
            <DialogTitle>{t.groups.create.title}</DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label={t.groups.create.schoolSelect} required>
                  <Dropdown
                    value={schools.find((x) => x.id === schoolId)?.name || ""}
                    selectedOptions={[schoolId]}
                    onOptionSelect={(_, d) =>
                      setSchoolId(String(d.optionValue || ""))
                    }
                  >
                    {schools.map((sch) => (
                      <Option key={sch.id} value={sch.id} text={sch.name}>
                        {sch.name}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
                <Field label={t.groups.name} required>
                  <Input value={name} onChange={(_, d) => setName(d.value)} />
                </Field>
                <Field
                  label={t.groups.create.teacherSelect}
                  required
                  hint={
                    teachers && teachers.length === 0
                      ? t.groups.create.noTeachers
                      : t.groups.create.teacherHelp
                  }
                >
                  <Combobox
                    placeholder={t.groups.create.teacherPlaceholder}
                    disabled={teachers === null || teachers.length === 0}
                    value={
                      selectedTeacher
                        ? teacherLabel(selectedTeacher)
                        : teacherQuery
                    }
                    selectedOptions={teacherId ? [teacherId] : []}
                    onInput={(e) => {
                      setTeacherQuery((e.target as HTMLInputElement).value);
                      if (teacherId) setTeacherId("");
                    }}
                    onOptionSelect={(_, d) => {
                      const id = String(d.optionValue || "");
                      setTeacherId(id);
                      const t2 = (teachers || []).find((x) => x.id === id);
                      setTeacherQuery(t2 ? teacherLabel(t2) : "");
                    }}
                  >
                    {filteredTeachers.length === 0 ? (
                      <Option key="__none" value="" text="" disabled>
                        {t.groups.create.noMatches}
                      </Option>
                    ) : (
                      filteredTeachers.map((tt) => (
                        <Option
                          key={tt.id}
                          value={tt.id}
                          text={teacherLabel(tt)}
                        >
                          {teacherLabel(tt)}
                        </Option>
                      ))
                    )}
                  </Combobox>
                </Field>
              </div>
            </DialogContent>
            <DialogActions>
              <Button type="button" onClick={onClose} disabled={busy}>
                {t.common.cancel}
              </Button>
              <Button appearance="primary" type="submit" disabled={busy}>
                {busy ? t.common.loading : t.groups.create.submit}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  );
}

function ManageMembersDialog({
  group,
  onClose,
}: {
  group: Group;
  onClose: () => void;
}) {
  const s = useStyles();
  const [members, setMembers] = useState<Child[] | null>(null);
  const [childId, setChildId] = useState("");
  const [err, setErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const list = await groupsApi.listMembers(group.id);
      setMembers(list);
    } catch {
      setErr(t.common.networkError);
    }
  }, [group.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function add() {
    setErr(undefined);
    if (!childId.trim()) return;
    setBusy(true);
    try {
      await groupsApi.addMember(group.id, childId.trim());
      setChildId("");
      load();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409)
        setErr(t.groups.members.schoolMismatch);
      else if (e instanceof ApiError && e.status === 404)
        setErr(t.groups.members.notFound);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  async function remove(cid: string) {
    setBusy(true);
    try {
      await groupsApi.removeMember(group.id, cid);
      load();
    } catch {
      setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>
            {t.groups.members.title}: {group.name}
          </DialogTitle>
          <DialogContent>
            {err && (
              <MessageBar intent="error" style={{ marginBottom: 12 }}>
                <MessageBarBody>{err}</MessageBarBody>
              </MessageBar>
            )}
            <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
              <Field
                label={t.groups.members.childIdLabel}
                hint={t.groups.members.childIdHelp}
                style={{ flex: 1 }}
              >
                <Input value={childId} onChange={(_, d) => setChildId(d.value)} />
              </Field>
              <Button
                appearance="primary"
                onClick={add}
                disabled={busy || !childId.trim()}
                style={{ alignSelf: "end" }}
              >
                {t.groups.members.addChild}
              </Button>
            </div>

            {members === null ? (
              <Spinner label={t.common.loading} />
            ) : members.length === 0 ? (
              <Body1>{t.groups.members.empty}</Body1>
            ) : (
              <div className={s.membersList}>
                {members.map((m) => (
                  <div key={m.id} className={s.memberRow}>
                    <div>
                      <div>
                        {m.first_name} {m.last_name}
                      </div>
                      <div className={s.meta}>
                        {m.username || t.common.none} · {m.id}
                      </div>
                    </div>
                    <Button onClick={() => remove(m.id)} disabled={busy}>
                      {t.groups.members.remove}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>{t.common.close}</Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

function ManageProgrammesDialog({
  group,
  onClose,
}: {
  group: Group;
  onClose: () => void;
}) {
  const s = useStyles();
  const [assigned, setAssigned] = useState<string[] | null>(null);
  const [allProgrammes, setAllProgrammes] = useState<Programme[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [err, setErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const [gps, ps] = await Promise.all([
        groupProgrammesApi.list(group.id),
        programmesApi.list(),
      ]);
      setAssigned(gps.map((x) => x.programme_id));
      setAllProgrammes(ps);
    } catch {
      setErr(t.common.networkError);
    }
  }, [group.id]);

  useEffect(() => {
    load();
  }, [load]);

  const programmesById = useMemo(
    () => Object.fromEntries(allProgrammes.map((p) => [p.id, p])),
    [allProgrammes]
  );
  const available = useMemo(
    () =>
      allProgrammes.filter((p) => !(assigned || []).includes(p.id)),
    [allProgrammes, assigned]
  );

  useEffect(() => {
    if (selected && !available.find((p) => p.id === selected)) {
      setSelected("");
    }
  }, [available, selected]);

  async function add() {
    if (!selected) return;
    setBusy(true);
    setErr(undefined);
    try {
      await groupProgrammesApi.assign(group.id, selected);
      setSelected("");
      load();
    } catch (e) {
      if (e instanceof ApiError && e.status === 404)
        setErr(e.detail || t.common.error);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  async function remove(pid: string) {
    setBusy(true);
    try {
      await groupProgrammesApi.unassign(group.id, pid);
      load();
    } catch {
      setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>
            {t.groupProgrammes.title}: {group.name}
          </DialogTitle>
          <DialogContent>
            {err && (
              <MessageBar intent="error" style={{ marginBottom: 12 }}>
                <MessageBarBody>{err}</MessageBarBody>
              </MessageBar>
            )}
            <Body1 style={{ marginBottom: 12 }}>
              {t.groupProgrammes.intro}
            </Body1>

            <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
              <Field
                label={t.groupProgrammes.selectProgramme}
                style={{ flex: 1 }}
              >
                <Dropdown
                  disabled={available.length === 0}
                  value={
                    selected
                      ? programmesById[selected]?.name || selected
                      : available.length === 0
                      ? t.groupProgrammes.noneAvailable
                      : ""
                  }
                  selectedOptions={selected ? [selected] : []}
                  onOptionSelect={(_, d) =>
                    setSelected(String(d.optionValue || ""))
                  }
                >
                  {available.map((p) => (
                    <Option key={p.id} value={p.id} text={p.name}>
                      {p.name} · {p.language}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
              <Button
                appearance="primary"
                onClick={add}
                disabled={busy || !selected}
                style={{ alignSelf: "end" }}
              >
                {t.groupProgrammes.add}
              </Button>
            </div>

            {assigned === null ? (
              <Spinner label={t.common.loading} />
            ) : assigned.length === 0 ? (
              <Body1>{t.groupProgrammes.empty}</Body1>
            ) : (
              <div className={s.membersList}>
                {assigned.map((pid) => {
                  const p = programmesById[pid];
                  return (
                    <div key={pid} className={s.memberRow}>
                      <div>
                        <div>{p?.name || pid}</div>
                        <div className={s.meta}>
                          {p?.language || ""} · {pid}
                        </div>
                      </div>
                      <Button onClick={() => remove(pid)} disabled={busy}>
                        {t.groupProgrammes.remove}
                      </Button>
                    </div>
                  );
                })}
              </div>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>{t.common.close}</Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}
