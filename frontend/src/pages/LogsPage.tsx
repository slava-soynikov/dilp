import { useCallback, useEffect, useState } from "react";
import {
  Body1,
  Button,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Select,
  Tab,
  TabList,
  Title2,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ApiError } from "../api/client";
import {
  logsApi,
  type ActivityLog,
  type AuditLog,
  type LogQuery,
} from "../api/logs";
import { t } from "../i18n/ru";

type TabKey = "activity" | "audit";

const ACTIVITY_ACTIONS = [
  "register",
  "login",
  "logout",
  "password_forgot",
  "password_reset",
  "lesson_open",
  "module_start",
  "module_complete",
  "lesson_start",
  "lesson_complete",
  "consent_grant",
  "consent_revoke",
];

const AUDIT_ACTIONS = ["create", "update", "delete"];

const AUDIT_ENTITY_TYPES = [
  "users",
  "user_roles",
  "child_profiles",
  "parent_profiles",
  "teacher_profiles",
  "parent_child_relations",
  "consents",
  "group_members",
];

const ACTIVITY_ENTITY_TYPES = ["user", "lesson", "module", "consent"];

const useStyles = makeStyles({
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
    flexWrap: "wrap",
    gap: "12px",
  },
  intro: { marginBottom: "16px" },
  filterBox: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "12px",
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.padding("16px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    marginBottom: "16px",
  },
  filterActions: { display: "flex", gap: "8px", marginTop: "12px" },
  table: {
    width: "100%",
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    borderCollapse: "collapse",
    overflow: "hidden",
    tableLayout: "fixed",
  },
  th: {
    textAlign: "left",
    ...shorthands.padding("12px", "16px"),
    backgroundColor: tokens.colorNeutralBackground2,
    fontWeight: 600,
    fontSize: "13px",
  },
  td: {
    ...shorthands.padding("12px", "16px"),
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: "14px",
    verticalAlign: "top",
    wordBreak: "break-all",
  },
  mono: { fontFamily: "monospace", fontSize: "12px" },
  pager: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
    justifyContent: "flex-end",
    marginTop: "12px",
  },
  muted: { color: tokens.colorNeutralForeground3, fontSize: "12px" },
  diffPre: {
    fontFamily: "monospace",
    fontSize: "12px",
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.padding("8px", "12px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    marginTop: "8px",
    maxHeight: "320px",
    overflow: "auto",
  },
});

function fmtTs(s: string): string {
  try {
    return new Date(s).toLocaleString("ru-RU");
  } catch {
    return s;
  }
}

function actorLabel(userId: string | null): string {
  return userId ?? t.logs.systemActor;
}

function shortId(id: string | null | undefined): string {
  if (!id) return t.logs.diffNone;
  return id.length > 12 ? `${id.slice(0, 8)}…` : id;
}

export default function LogsPage() {
  const s = useStyles();
  const [tab, setTab] = useState<TabKey>("activity");
  return (
    <AppShell>
      <div className={s.header}>
        <Title2>{t.logs.title}</Title2>
      </div>
      <Body1 className={s.intro}>{t.logs.intro}</Body1>
      <TabList
        selectedValue={tab}
        onTabSelect={(_, d) => setTab(d.value as TabKey)}
        style={{ marginBottom: 16 }}
      >
        <Tab value="activity">{t.logs.tabActivity}</Tab>
        <Tab value="audit">{t.logs.tabAudit}</Tab>
      </TabList>
      {tab === "activity" ? <ActivityPanel /> : <AuditPanel />}
    </AppShell>
  );
}

function FiltersBar({
  available,
  filters,
  setFilters,
  onApply,
  onClear,
  withEntityId,
}: {
  available: { actions: string[]; entityTypes: string[] };
  filters: LogQuery;
  setFilters: (q: LogQuery) => void;
  onApply: () => void;
  onClear: () => void;
  withEntityId?: boolean;
}) {
  const s = useStyles();
  return (
    <>
      <div className={s.filterBox}>
        <Field label={t.logs.filterAction}>
          <Select
            value={filters.action || ""}
            onChange={(_, d) =>
              setFilters({ ...filters, action: d.value || undefined })
            }
          >
            <option value="">—</option>
            {available.actions.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t.logs.filterEntityType}>
          <Select
            value={filters.entity_type || ""}
            onChange={(_, d) =>
              setFilters({ ...filters, entity_type: d.value || undefined })
            }
          >
            <option value="">—</option>
            {available.entityTypes.map((et) => (
              <option key={et} value={et}>
                {et}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t.logs.filterUserId}>
          <Input
            value={filters.user_id || ""}
            onChange={(_, d) =>
              setFilters({ ...filters, user_id: d.value || undefined })
            }
          />
        </Field>
        {withEntityId && (
          <Field label={t.logs.filterEntityId}>
            <Input
              value={filters.entity_id || ""}
              onChange={(_, d) =>
                setFilters({ ...filters, entity_id: d.value || undefined })
              }
            />
          </Field>
        )}
      </div>
      <div className={s.filterActions}>
        <Button appearance="primary" onClick={onApply}>
          {t.logs.applyFilters}
        </Button>
        <Button onClick={onClear}>{t.logs.clearFilters}</Button>
      </div>
    </>
  );
}

function Pager({
  page,
  pageSize,
  rows,
  onPrev,
  onNext,
  onRefresh,
  onPageSize,
}: {
  page: number;
  pageSize: number;
  rows: number;
  onPrev: () => void;
  onNext: () => void;
  onRefresh: () => void;
  onPageSize: (n: number) => void;
}) {
  const s = useStyles();
  return (
    <div className={s.pager}>
      <Button onClick={onRefresh}>{t.logs.refresh}</Button>
      <span className={s.muted}>
        {t.logs.page} {page + 1}
      </span>
      <Select
        value={String(pageSize)}
        onChange={(_, d) => onPageSize(Number(d.value))}
      >
        {[25, 50, 100, 200].map((n) => (
          <option key={n} value={n}>
            {n} {t.logs.pageSize}
          </option>
        ))}
      </Select>
      <Button onClick={onPrev} disabled={page === 0}>
        {t.logs.prev}
      </Button>
      <Button onClick={onNext} disabled={rows < pageSize}>
        {t.logs.next}
      </Button>
    </div>
  );
}

function ActivityPanel() {
  const s = useStyles();
  const [filters, setFilters] = useState<LogQuery>({});
  const [applied, setApplied] = useState<LogQuery>({});
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [rows, setRows] = useState<ActivityLog[]>([]);
  const [err, setErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setErr(undefined);
    try {
      const data = await logsApi.activity({
        ...applied,
        limit: pageSize,
        offset: page * pageSize,
      });
      setRows(data);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403)
        setErr(t.logs.accessDenied);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }, [applied, page, pageSize]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <FiltersBar
        available={{
          actions: ACTIVITY_ACTIONS,
          entityTypes: ACTIVITY_ENTITY_TYPES,
        }}
        filters={filters}
        setFilters={setFilters}
        onApply={() => {
          setApplied(filters);
          setPage(0);
        }}
        onClear={() => {
          setFilters({});
          setApplied({});
          setPage(0);
        }}
      />
      {err && (
        <MessageBar intent="error" style={{ margin: "12px 0" }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}
      <table className={s.table}>
        <thead>
          <tr>
            <th className={s.th} style={{ width: "20%" }}>{t.logs.colTime}</th>
            <th className={s.th} style={{ width: "20%" }}>{t.logs.colAction}</th>
            <th className={s.th} style={{ width: "30%" }}>{t.logs.colEntity}</th>
            <th className={s.th} style={{ width: "30%" }}>{t.logs.colUser}</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && !busy && (
            <tr>
              <td className={s.td} colSpan={4}>
                {t.logs.empty}
              </td>
            </tr>
          )}
          {rows.map((r) => (
            <tr key={r.id}>
              <td className={s.td}>{fmtTs(r.created_at)}</td>
              <td className={s.td}>{r.action}</td>
              <td className={s.td}>
                {r.entity_type ? (
                  <>
                    <strong>{r.entity_type}</strong>
                    <div className={s.mono} title={r.entity_id || ""}>
                      {shortId(r.entity_id)}
                    </div>
                  </>
                ) : (
                  t.logs.diffNone
                )}
              </td>
              <td className={`${s.td} ${s.mono}`}>{actorLabel(r.user_id)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pager
        page={page}
        pageSize={pageSize}
        rows={rows.length}
        onPrev={() => setPage((p) => Math.max(0, p - 1))}
        onNext={() => setPage((p) => p + 1)}
        onRefresh={load}
        onPageSize={(n) => {
          setPageSize(n);
          setPage(0);
        }}
      />
    </>
  );
}

function AuditPanel() {
  const s = useStyles();
  const [filters, setFilters] = useState<LogQuery>({});
  const [applied, setApplied] = useState<LogQuery>({});
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [rows, setRows] = useState<AuditLog[]>([]);
  const [err, setErr] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setBusy(true);
    setErr(undefined);
    try {
      const data = await logsApi.audit({
        ...applied,
        limit: pageSize,
        offset: page * pageSize,
      });
      setRows(data);
      setExpanded(new Set());
    } catch (e) {
      if (e instanceof ApiError && e.status === 403)
        setErr(t.logs.accessDenied);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }, [applied, page, pageSize]);

  useEffect(() => {
    load();
  }, [load]);

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function prettyDiff(raw: string | null): string {
    if (!raw) return t.logs.diffNone;
    try {
      return JSON.stringify(JSON.parse(raw), null, 2);
    } catch {
      return raw;
    }
  }

  return (
    <>
      <FiltersBar
        available={{
          actions: AUDIT_ACTIONS,
          entityTypes: AUDIT_ENTITY_TYPES,
        }}
        filters={filters}
        setFilters={setFilters}
        onApply={() => {
          setApplied(filters);
          setPage(0);
        }}
        onClear={() => {
          setFilters({});
          setApplied({});
          setPage(0);
        }}
        withEntityId
      />
      {err && (
        <MessageBar intent="error" style={{ margin: "12px 0" }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}
      <table className={s.table}>
        <thead>
          <tr>
            <th className={s.th} style={{ width: "18%" }}>{t.logs.colTime}</th>
            <th className={s.th} style={{ width: "14%" }}>{t.logs.colAction}</th>
            <th className={s.th} style={{ width: "28%" }}>{t.logs.colEntity}</th>
            <th className={s.th} style={{ width: "22%" }}>{t.logs.colUser}</th>
            <th className={s.th} style={{ width: "18%" }}>{t.logs.colDiff}</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && !busy && (
            <tr>
              <td className={s.td} colSpan={5}>
                {t.logs.empty}
              </td>
            </tr>
          )}
          {rows.map((r) => {
            const open = expanded.has(r.id);
            return (
              <>
                <tr key={r.id}>
                  <td className={s.td}>{fmtTs(r.timestamp)}</td>
                  <td className={s.td}>{r.action}</td>
                  <td className={s.td}>
                    <strong>{r.entity_type}</strong>
                    <div className={s.mono} title={r.entity_id}>
                      {shortId(r.entity_id)}
                    </div>
                  </td>
                  <td className={`${s.td} ${s.mono}`}>
                    {actorLabel(r.user_id)}
                  </td>
                  <td className={s.td}>
                    <Button
                      appearance="subtle"
                      size="small"
                      onClick={() => toggle(r.id)}
                      disabled={!r.diff}
                    >
                      {open ? t.logs.diffHide : t.logs.diffShow}
                    </Button>
                  </td>
                </tr>
                {open && (
                  <tr key={`${r.id}-diff`}>
                    <td className={s.td} colSpan={5}>
                      <pre className={s.diffPre}>{prettyDiff(r.diff)}</pre>
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
      <Pager
        page={page}
        pageSize={pageSize}
        rows={rows.length}
        onPrev={() => setPage((p) => Math.max(0, p - 1))}
        onNext={() => setPage((p) => p + 1)}
        onRefresh={load}
        onPageSize={(n) => {
          setPageSize(n);
          setPage(0);
        }}
      />
    </>
  );
}