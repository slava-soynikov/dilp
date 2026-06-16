import { api } from "./client";

// ---- /reports/active-users ----

export type ActiveUsersByRole = {
  parent: number;
  child: number;
  teacher: number;
  admin: number;
  auditor: number;
};

export type ActiveUsersReport = {
  window_days: number;
  since: string;
  total_active: number;
  by_role: ActiveUsersByRole;
};

// ---- /reports/activity-overview ----

export type ActionCount = { action: string; count: number };
export type DayCount = { date: string; count: number };

export type ActivityOverviewReport = {
  window_days: number;
  since: string;
  total_events: number;
  by_action: ActionCount[];
  by_day: DayCount[];
};

// ---- /reports/groups/{id}/progress ----

export type GroupProgrammeProgress = {
  programme_id: string;
  programme_name: string;
  modules_total: number;
  modules_completed_total: number;
  completion_avg_pct: number;
};

export type GroupProgressReport = {
  group_id: string;
  member_count: number;
  programmes: GroupProgrammeProgress[];
};

// ---- /reports/programmes/{id}/funnel ----

export type ProgrammeFunnelModule = {
  module_id: string;
  title: string;
  order_index: number;
  started: number;
  completed: number;
};

export type ProgrammeFunnelReport = {
  programme_id: string;
  total_children: number;
  modules: ProgrammeFunnelModule[];
};

// ---- /parents/me/children/{id}/dashboard ----

export type ChildModuleSummary = {
  module_id: string;
  title: string;
  order_index: number;
  status: "not_started" | "in_progress" | "completed";
  lessons_total: number;
  lessons_completed: number;
};

export type ChildProgrammeSummary = {
  programme_id: string;
  name: string;
  modules: ChildModuleSummary[];
};

export type ChildDashboardReport = {
  child_id: string;
  programmes: ChildProgrammeSummary[];
};

export const reportsApi = {
  activeUsers: (window_days = 30) =>
    api<ActiveUsersReport>(
      `/reports/active-users?window_days=${window_days}`,
      { method: "GET", auth: true }
    ),

  activityOverview: (window_days = 30) =>
    api<ActivityOverviewReport>(
      `/reports/activity-overview?window_days=${window_days}`,
      { method: "GET", auth: true }
    ),

  groupProgress: (group_id: string) =>
    api<GroupProgressReport>(`/reports/groups/${group_id}/progress`, {
      method: "GET",
      auth: true,
    }),

  programmeFunnel: (programme_id: string) =>
    api<ProgrammeFunnelReport>(
      `/reports/programmes/${programme_id}/funnel`,
      { method: "GET", auth: true }
    ),

  childDashboard: (child_id: string) =>
    api<ChildDashboardReport>(
      `/parents/me/children/${child_id}/dashboard`,
      { method: "GET", auth: true }
    ),
};