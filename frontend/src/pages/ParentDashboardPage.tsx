/**
 * Sprint 7 — parent dashboard view for a single child.
 *
 * GET /parents/me/children/{child_id}/dashboard (§5.1, §7.3).
 *  - Only the linked parent can read; the backend returns 404 for unrelated
 *    children (do not leak existence), and this page surfaces that as
 *    "child not found".
 *  - The parent can switch between their own children using a selector.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Body1,
  MessageBar,
  MessageBarBody,
  Select,
  Spinner,
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ApiError } from "../api/client";
import { childrenApi, type Child } from "../api/children";
import {
  reportsApi,
  type ChildDashboardReport,
  type ChildModuleSummary,
} from "../api/reports";
import { t } from "../i18n/ru";

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
  filterRow: {
    display: "flex",
    gap: "12px",
    alignItems: "flex-end",
    flexWrap: "wrap",
    marginBottom: "16px",
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
    verticalAlign: "middle",
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
  badge: {
    display: "inline-block",
    fontSize: "11px",
    fontWeight: 600,
    ...shorthands.padding("2px", "8px"),
    ...shorthands.borderRadius(tokens.borderRadiusCircular),
    color: tokens.colorNeutralForegroundOnBrand,
  },
  muted: { color: tokens.colorNeutralForeground3, fontSize: "12px" },
  empty: {
    color: tokens.colorNeutralForeground3,
    fontStyle: "italic",
    ...shorthands.padding("12px"),
  },
});

function statusColor(status: ChildModuleSummary["status"]): string {
  if (status === "completed") return tokens.colorPaletteGreenBackground3;
  if (status === "in_progress") return tokens.colorPaletteYellowBackground3;
  return tokens.colorNeutralBackground3;
}

function statusLabel(status: ChildModuleSummary["status"]): string {
  if (status === "completed") return t.reports.statusCompleted;
  if (status === "in_progress") return t.reports.statusInProgress;
  return t.reports.statusNotStarted;
}

function lessonPct(m: ChildModuleSummary): number {
  if (m.lessons_total === 0) return 0;
  return (m.lessons_completed / m.lessons_total) * 100;
}

export default function ParentDashboardPage() {
  const s = useStyles();
  const navigate = useNavigate();
  const { childId: paramChildId } = useParams<{ childId?: string }>();

  const [children, setChildren] = useState<Child[]>([]);
  const [dashboard, setDashboard] = useState<ChildDashboardReport>();
  const [err, setErr] = useState<string>();
  const [bootBusy, setBootBusy] = useState(true);
  const [busy, setBusy] = useState(false);

  // Bootstrap the parent's own children.
  useEffect(() => {
    (async () => {
      setBootBusy(true);
      try {
        const list = await childrenApi.list();
        setChildren(list);
        if (!paramChildId && list.length > 0) {
          navigate(`/parent-dashboard/${list[0].id}`, { replace: true });
        }
      } catch {
        setErr(t.common.networkError);
      } finally {
        setBootBusy(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = useCallback(async (id: string) => {
    setBusy(true);
    setErr(undefined);
    try {
      setDashboard(await reportsApi.childDashboard(id));
    } catch (e) {
      setDashboard(undefined);
      if (e instanceof ApiError && e.status === 404)
        setErr(t.reports.childNotFound);
      else if (e instanceof ApiError && e.status === 403)
        setErr(t.reports.accessDenied);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (paramChildId) void load(paramChildId);
  }, [paramChildId, load]);

  const childName = useMemo(() => {
    const c = children.find((x) => x.id === paramChildId);
    if (!c) return "";
    return `${c.first_name} ${c.last_name}`.trim();
  }, [children, paramChildId]);

  if (bootBusy) {
    return (
      <AppShell>
        <Spinner label={t.common.loading} />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className={s.header}>
        <Title2>{t.reports.parentDashboardTitle}</Title2>
      </div>
      <Body1 className={s.intro}>{t.reports.parentDashboardIntro}</Body1>

      {children.length === 0 ? (
        <MessageBar intent="info">
          <MessageBarBody>{t.reports.noChildren}</MessageBarBody>
        </MessageBar>
      ) : (
        <div className={s.filterRow}>
          <Select
            value={paramChildId || ""}
            onChange={(_, d) => navigate(`/parent-dashboard/${d.value}`)}
            style={{ minWidth: 280 }}
          >
            {children.map((c) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name}
                {c.username ? ` — ${c.username}` : ""}
              </option>
            ))}
          </Select>
        </div>
      )}

      {err && (
        <MessageBar intent="error" style={{ margin: "12px 0" }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {busy && <Spinner size="small" label={t.common.loading} />}

      {dashboard && !busy && (
        <>
          {childName && (
            <Title3 style={{ marginBottom: 12 }}>{childName}</Title3>
          )}
          {dashboard.programmes.length === 0 ? (
            <div className={`${s.section} ${s.empty}`}>
              {t.reports.noProgrammesForChild}
            </div>
          ) : (
            dashboard.programmes.map((p) => (
              <div key={p.programme_id} className={s.section}>
                <Title3 style={{ marginBottom: 12 }}>{p.name}</Title3>
                <table className={s.table}>
                  <thead>
                    <tr>
                      <th className={s.th} style={{ width: "8%" }}>
                        #
                      </th>
                      <th className={s.th}>{t.reports.colModule}</th>
                      <th className={s.th} style={{ width: "18%" }}>
                        {t.reports.colStatus}
                      </th>
                      <th className={s.th} style={{ width: "30%" }}>
                        {t.reports.colLessons}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {p.modules.map((m) => {
                      const pct = lessonPct(m);
                      return (
                        <tr key={m.module_id}>
                          <td className={s.td}>{m.order_index}</td>
                          <td className={s.td}>{m.title}</td>
                          <td className={s.td}>
                            <span
                              className={s.badge}
                              style={{ backgroundColor: statusColor(m.status) }}
                            >
                              {statusLabel(m.status)}
                            </span>
                          </td>
                          <td className={s.td}>
                            <div className={s.bar} style={{ marginBottom: 4 }}>
                              <div
                                className={s.barFill}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <div className={s.muted}>
                              {m.lessons_completed} / {m.lessons_total}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ))
          )}
        </>
      )}
    </AppShell>
  );
}