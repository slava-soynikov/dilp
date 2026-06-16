/**
 * Sprint 7 reporting surface (§5.1 / §7.3).
 *
 * Role-aware:
 *  - admin / auditor see the global tab (active users + activity overview) and
 *    can pick any group / programme for drill-down.
 *  - teacher sees only the drill-down tab, restricted to groups they own /
 *    programmes assigned to one of their groups.
 *  - other roles never reach this page (RequireRole guard in App.tsx).
 *
 * All numbers come from the aggregated `/reports/*` endpoints, which never
 * expose `user_id` (§7 Data Minimization).
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Body1,
  Button,
  Field,
  MessageBar,
  MessageBarBody,
  Select,
  Spinner,
  Tab,
  TabList,
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { groupsApi, type Group } from "../api/groups";
import { programmesApi, type Programme } from "../api/programmes";
import {
  reportsApi,
  type ActiveUsersReport,
  type ActivityOverviewReport,
  type GroupProgressReport,
  type ProgrammeFunnelReport,
} from "../api/reports";
import { t } from "../i18n/ru";

type TabKey = "global" | "drill";

const WINDOW_CHOICES = [7, 30, 90, 180, 365];

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
  cardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
    marginBottom: "24px",
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.padding("16px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
  },
  metric: {
    fontSize: "32px",
    fontWeight: 600,
    lineHeight: 1.1,
  },
  metricLabel: {
    fontSize: "13px",
    color: tokens.colorNeutralForeground3,
    marginTop: "4px",
  },
  section: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.padding("16px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    marginBottom: "16px",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "14px",
  },
  th: {
    textAlign: "left",
    ...shorthands.padding("8px", "12px"),
    backgroundColor: tokens.colorNeutralBackground2,
    fontWeight: 600,
    fontSize: "12px",
  },
  td: {
    ...shorthands.padding("10px", "12px"),
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    verticalAlign: "top",
  },
  filterRow: {
    display: "flex",
    gap: "12px",
    alignItems: "flex-end",
    flexWrap: "wrap",
    marginBottom: "16px",
  },
  bar: {
    position: "relative",
    height: "10px",
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    overflow: "hidden",
    minWidth: "120px",
  },
  barFill: {
    position: "absolute",
    top: 0,
    left: 0,
    bottom: 0,
    backgroundColor: tokens.colorBrandBackground,
  },
  muted: { color: tokens.colorNeutralForeground3, fontSize: "12px" },
  empty: {
    color: tokens.colorNeutralForeground3,
    fontStyle: "italic",
    ...shorthands.padding("12px"),
  },
});

function fmtPct(n: number): string {
  return `${n.toFixed(1).replace(".", ",")} %`;
}

function fmtDate(s: string): string {
  try {
    return new Date(s).toLocaleDateString("ru-RU");
  } catch {
    return s;
  }
}

export default function ReportsPage() {
  const s = useStyles();
  const { hasRole } = useAuth();
  const canSeeGlobal = hasRole("admin") || hasRole("auditor");
  const [tab, setTab] = useState<TabKey>(canSeeGlobal ? "global" : "drill");

  return (
    <AppShell>
      <div className={s.header}>
        <Title2>{t.reports.title}</Title2>
      </div>
      <Body1 className={s.intro}>{t.reports.intro}</Body1>
      <TabList
        selectedValue={tab}
        onTabSelect={(_, d) => setTab(d.value as TabKey)}
        style={{ marginBottom: 16 }}
      >
        {canSeeGlobal && <Tab value="global">{t.reports.tabGlobal}</Tab>}
        <Tab value="drill">{t.reports.tabDrill}</Tab>
      </TabList>
      {tab === "global" && canSeeGlobal ? <GlobalPanel /> : <DrillPanel />}
    </AppShell>
  );
}

// ---------------- Global panel (admin/auditor only) ----------------

function GlobalPanel() {
  const s = useStyles();
  const [windowDays, setWindowDays] = useState(30);
  const [active, setActive] = useState<ActiveUsersReport>();
  const [overview, setOverview] = useState<ActivityOverviewReport>();
  const [err, setErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setErr(undefined);
    try {
      const [a, o] = await Promise.all([
        reportsApi.activeUsers(windowDays),
        reportsApi.activityOverview(windowDays),
      ]);
      setActive(a);
      setOverview(o);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403)
        setErr(t.reports.accessDenied);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }, [windowDays]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <div className={s.filterRow}>
        <Field label={t.reports.windowDays}>
          <Select
            value={String(windowDays)}
            onChange={(_, d) => setWindowDays(Number(d.value))}
          >
            {WINDOW_CHOICES.map((n) => (
              <option key={n} value={n}>
                {n} {t.reports.days}
              </option>
            ))}
          </Select>
        </Field>
        <Button onClick={load} disabled={busy}>
          {t.reports.refresh}
        </Button>
        {busy && <Spinner size="tiny" />}
      </div>

      {err && (
        <MessageBar intent="error" style={{ margin: "12px 0" }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {active && (
        <>
          <Title3 style={{ marginBottom: 12 }}>
            {t.reports.activeUsersTitle}
          </Title3>
          <Body1 className={s.muted} style={{ marginBottom: 12 }}>
            {t.reports.since}: {fmtDate(active.since)}
          </Body1>
          <div className={s.cardGrid}>
            <Metric label={t.reports.totalActive} value={active.total_active} />
            <Metric label={t.roles.parent} value={active.by_role.parent} />
            <Metric label={t.roles.child} value={active.by_role.child} />
            <Metric label={t.roles.teacher} value={active.by_role.teacher} />
            <Metric label={t.roles.admin} value={active.by_role.admin} />
            <Metric label={t.roles.auditor} value={active.by_role.auditor} />
          </div>
        </>
      )}

      {overview && (
        <>
          <Title3 style={{ marginBottom: 12 }}>
            {t.reports.activityOverviewTitle}
          </Title3>
          <div className={s.cardGrid}>
            <Metric
              label={t.reports.totalEvents}
              value={overview.total_events}
            />
          </div>
          <div className={s.section}>
            <Title3 style={{ marginBottom: 12 }}>
              {t.reports.byAction}
            </Title3>
            {overview.by_action.length === 0 ? (
              <div className={s.empty}>{t.reports.empty}</div>
            ) : (
              <BarTable
                rows={overview.by_action.map((r) => ({
                  label: r.action,
                  value: r.count,
                }))}
              />
            )}
          </div>
          <div className={s.section}>
            <Title3 style={{ marginBottom: 12 }}>{t.reports.byDay}</Title3>
            {overview.by_day.length === 0 ? (
              <div className={s.empty}>{t.reports.empty}</div>
            ) : (
              <BarTable
                rows={overview.by_day.map((r) => ({
                  label: fmtDate(r.date),
                  value: r.count,
                }))}
              />
            )}
          </div>
        </>
      )}
    </>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  const s = useStyles();
  return (
    <div className={s.card}>
      <div className={s.metric}>{value}</div>
      <div className={s.metricLabel}>{label}</div>
    </div>
  );
}

function BarTable({ rows }: { rows: { label: string; value: number }[] }) {
  const s = useStyles();
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <table className={s.table}>
      <tbody>
        {rows.map((r) => (
          <tr key={r.label}>
            <td className={s.td} style={{ width: "30%" }}>
              {r.label}
            </td>
            <td className={s.td} style={{ width: "55%" }}>
              <div className={s.bar}>
                <div
                  className={s.barFill}
                  style={{ width: `${(r.value / max) * 100}%` }}
                />
              </div>
            </td>
            <td
              className={s.td}
              style={{ width: "15%", textAlign: "right", fontVariantNumeric: "tabular-nums" }}
            >
              {r.value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ---------------- Drill-down panel (admin/auditor/teacher) ----------------

function DrillPanel() {
  const s = useStyles();
  const [groups, setGroups] = useState<Group[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [groupId, setGroupId] = useState<string>("");
  const [programmeId, setProgrammeId] = useState<string>("");
  const [groupReport, setGroupReport] = useState<GroupProgressReport>();
  const [funnel, setFunnel] = useState<ProgrammeFunnelReport>();
  const [err, setErr] = useState<string>();
  const [bootBusy, setBootBusy] = useState(true);

  useEffect(() => {
    (async () => {
      setBootBusy(true);
      try {
        const [gs, ps] = await Promise.all([
          groupsApi.list(),
          programmesApi.list(),
        ]);
        setGroups(gs);
        setProgrammes(ps);
      } catch {
        setErr(t.common.networkError);
      } finally {
        setBootBusy(false);
      }
    })();
  }, []);

  const loadGroup = useCallback(async (id: string) => {
    if (!id) {
      setGroupReport(undefined);
      return;
    }
    try {
      setGroupReport(await reportsApi.groupProgress(id));
      setErr(undefined);
    } catch (e) {
      setGroupReport(undefined);
      if (e instanceof ApiError && (e.status === 403 || e.status === 404))
        setErr(t.reports.accessDeniedScope);
      else setErr(t.common.networkError);
    }
  }, []);

  const loadFunnel = useCallback(async (id: string) => {
    if (!id) {
      setFunnel(undefined);
      return;
    }
    try {
      setFunnel(await reportsApi.programmeFunnel(id));
      setErr(undefined);
    } catch (e) {
      setFunnel(undefined);
      if (e instanceof ApiError && (e.status === 403 || e.status === 404))
        setErr(t.reports.accessDeniedScope);
      else setErr(t.common.networkError);
    }
  }, []);

  useEffect(() => {
    if (groupId) void loadGroup(groupId);
  }, [groupId, loadGroup]);

  useEffect(() => {
    if (programmeId) void loadFunnel(programmeId);
  }, [programmeId, loadFunnel]);

  const programmeNameById = useMemo(
    () => Object.fromEntries(programmes.map((p) => [p.id, p.name])),
    [programmes]
  );

  if (bootBusy) return <Spinner label={t.common.loading} />;

  return (
    <>
      {err && (
        <MessageBar intent="error" style={{ margin: "12px 0" }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      <div className={s.filterRow}>
        <Field label={t.reports.selectGroup}>
          <Select
            value={groupId}
            onChange={(_, d) => setGroupId(d.value)}
          >
            <option value="">—</option>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t.reports.selectProgramme}>
          <Select
            value={programmeId}
            onChange={(_, d) => setProgrammeId(d.value)}
          >
            <option value="">—</option>
            {programmes.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      {groupReport && (
        <div className={s.section}>
          <Title3 style={{ marginBottom: 12 }}>
            {t.reports.groupProgressTitle}
          </Title3>
          <div className={s.cardGrid}>
            <Metric
              label={t.reports.memberCount}
              value={groupReport.member_count}
            />
            <Metric
              label={t.reports.assignedProgrammes}
              value={groupReport.programmes.length}
            />
          </div>
          {groupReport.programmes.length === 0 ? (
            <div className={s.empty}>{t.reports.noProgrammes}</div>
          ) : (
            <table className={s.table}>
              <thead>
                <tr>
                  <th className={s.th}>{t.reports.colProgramme}</th>
                  <th className={s.th}>{t.reports.colModulesTotal}</th>
                  <th className={s.th}>{t.reports.colCompletedTotal}</th>
                  <th className={s.th}>{t.reports.colCompletionPct}</th>
                </tr>
              </thead>
              <tbody>
                {groupReport.programmes.map((p) => (
                  <tr key={p.programme_id}>
                    <td className={s.td}>
                      {p.programme_name}
                      <div className={s.muted}>
                        {programmeNameById[p.programme_id] ? "" : p.programme_id}
                      </div>
                    </td>
                    <td className={s.td}>{p.modules_total}</td>
                    <td className={s.td}>{p.modules_completed_total}</td>
                    <td className={s.td}>
                      <div className={s.bar} style={{ marginBottom: 4 }}>
                        <div
                          className={s.barFill}
                          style={{ width: `${p.completion_avg_pct}%` }}
                        />
                      </div>
                      {fmtPct(p.completion_avg_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {funnel && (
        <div className={s.section}>
          <Title3 style={{ marginBottom: 12 }}>
            {t.reports.funnelTitle}
          </Title3>
          <div className={s.cardGrid}>
            <Metric
              label={t.reports.totalChildren}
              value={funnel.total_children}
            />
            <Metric
              label={t.reports.modulesTotal}
              value={funnel.modules.length}
            />
          </div>
          {funnel.modules.length === 0 ? (
            <div className={s.empty}>{t.reports.empty}</div>
          ) : (
            <table className={s.table}>
              <thead>
                <tr>
                  <th className={s.th} style={{ width: "10%" }}>
                    #
                  </th>
                  <th className={s.th}>{t.reports.colModule}</th>
                  <th className={s.th} style={{ width: "18%" }}>
                    {t.reports.colStarted}
                  </th>
                  <th className={s.th} style={{ width: "18%" }}>
                    {t.reports.colCompleted}
                  </th>
                  <th className={s.th} style={{ width: "28%" }}>
                    {t.reports.colFunnelRate}
                  </th>
                </tr>
              </thead>
              <tbody>
                {funnel.modules.map((m) => {
                  const total = Math.max(1, funnel.total_children);
                  const startedPct = (m.started / total) * 100;
                  const completedPct = (m.completed / total) * 100;
                  return (
                    <tr key={m.module_id}>
                      <td className={s.td}>{m.order_index}</td>
                      <td className={s.td}>{m.title}</td>
                      <td className={s.td}>
                        <div className={s.bar}>
                          <div
                            className={s.barFill}
                            style={{ width: `${startedPct}%` }}
                          />
                        </div>
                        <div className={s.muted}>{m.started}</div>
                      </td>
                      <td className={s.td}>
                        <div className={s.bar}>
                          <div
                            className={s.barFill}
                            style={{ width: `${completedPct}%` }}
                          />
                        </div>
                        <div className={s.muted}>{m.completed}</div>
                      </td>
                      <td className={s.td}>
                        {fmtPct(completedPct)}{" "}
                        <span className={s.muted}>
                          ({t.reports.ofChildren})
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </>
  );
}