"""Sprint 7 — reporting response schemas.

Architecture refs:
- §5.1 Reporting (Basis): aktive Nutzer, Aktivitätsübersichten, aggregierte
  Auswertungen.
- §7 Data Minimization / Privacy by Default: responses are aggregated only.
"""
from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field


# ---------- /reports/active-users ----------


class ActiveUsersByRole(BaseModel):
    parent: int = 0
    child: int = 0
    teacher: int = 0
    admin: int = 0
    auditor: int = 0


class ActiveUsersReport(BaseModel):
    window_days: int
    since: datetime
    total_active: int
    by_role: ActiveUsersByRole


# ---------- /reports/activity-overview ----------


class ActionCount(BaseModel):
    action: str
    count: int


class DayCount(BaseModel):
    date: date
    count: int


class ActivityOverviewReport(BaseModel):
    window_days: int
    since: datetime
    total_events: int
    by_action: list[ActionCount]
    by_day: list[DayCount]


# ---------- /reports/groups/{id}/progress ----------


class GroupProgrammeProgress(BaseModel):
    programme_id: str
    programme_name: str
    modules_total: int
    modules_completed_total: int
    completion_avg_pct: float = Field(
        ..., description="Average completion percentage across group members (0–100)."
    )


class GroupProgressReport(BaseModel):
    group_id: str
    member_count: int
    programmes: list[GroupProgrammeProgress]


# ---------- /reports/programmes/{id}/funnel ----------


class ProgrammeFunnelModule(BaseModel):
    module_id: str
    title: str
    order_index: int
    started: int
    completed: int


class ProgrammeFunnelReport(BaseModel):
    programme_id: str
    total_children: int
    modules: list[ProgrammeFunnelModule]


# ---------- /parents/me/children/{id}/dashboard ----------


class ChildModuleSummary(BaseModel):
    module_id: str
    title: str
    order_index: int
    status: str  # not_started | in_progress | completed
    lessons_total: int
    lessons_completed: int


class ChildProgrammeSummary(BaseModel):
    programme_id: str
    name: str
    modules: list[ChildModuleSummary]


class ChildDashboardReport(BaseModel):
    child_id: str
    programmes: list[ChildProgrammeSummary]
