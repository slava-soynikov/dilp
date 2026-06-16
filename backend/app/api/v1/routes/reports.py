"""Sprint 7 — reporting endpoints (§5.1 Reporting Basis).

All responses are aggregated; no PII is exposed (§7 Data Minimization).
Access:
- ``/reports/active-users`` and ``/reports/activity-overview``: admin or auditor.
- ``/reports/groups/{id}/progress``: admin/auditor or the group's owning teacher.
- ``/reports/programmes/{id}/funnel``: admin/auditor or a teacher whose group
  has the programme assigned.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.report import (
    ActiveUsersReport,
    ActivityOverviewReport,
    GroupProgressReport,
    ProgrammeFunnelReport,
)
from app.service.report import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

_GLOBAL_READERS = ("admin", "auditor")


@router.get("/active-users", response_model=ActiveUsersReport)
def active_users(
    window_days: int = Query(default=30, ge=1, le=365),
    _: User = Depends(require_role(*_GLOBAL_READERS)),
    db: Session = Depends(get_db),
):
    return ReportService(db).active_users(window_days)


@router.get("/activity-overview", response_model=ActivityOverviewReport)
def activity_overview(
    window_days: int = Query(default=30, ge=1, le=365),
    _: User = Depends(require_role(*_GLOBAL_READERS)),
    db: Session = Depends(get_db),
):
    return ReportService(db).activity_overview(window_days)


@router.get(
    "/groups/{group_id}/progress",
    response_model=GroupProgressReport,
)
def group_progress(
    group_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Restrict to roles capable of seeing groups; service enforces ownership.
    return ReportService(db).group_progress(group_id, user)


@router.get(
    "/programmes/{programme_id}/funnel",
    response_model=ProgrammeFunnelReport,
)
def programme_funnel(
    programme_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReportService(db).programme_funnel(programme_id, user)