"""Sprint 7 — reporting service.

Architecture refs:
- §5.1 Reporting (Basis): active users, activity overview, group progress, funnel.
- §7 Privacy by Default + §7.3 RBAC scoping.

Authorization model (callers must enforce role precondition):
- ``active_users`` / ``activity_overview``: admin or auditor only.
- ``group_progress(group_id, user)``: admin/auditor see any; teacher sees only
  groups they own (TeacherProfile.id == Group.teacher_id).
- ``programme_funnel(programme_id, user)``: admin/auditor see any; teacher sees
  only programmes assigned (via GroupProgramme) to one of their groups.
- ``child_dashboard(child_id, user)``: only the parent linked via
  ParentChildRelation may read; 404 otherwise (do not leak existence).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.model.group import Group, GroupMember, GroupProgramme
from app.model.log import ActivityLog
from app.model.profile import (
    ChildProfile,
    ParentChildRelation,
    ParentProfile,
    TeacherProfile,
)
from app.model.programme import Lesson, Module, Programme
from app.model.progress import LessonProgress, ModuleProgress
from app.model.user import Role, User, UserRole


def _user_roles(db: Session, user_id: str) -> set[str]:
    rows = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return {r[0] for r in rows}


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------- active users ----------------

    def active_users(self, window_days: int) -> dict:
        since = datetime.utcnow() - timedelta(days=window_days)
        # distinct user_ids that produced any ActivityLog in the window
        active_ids = {
            uid
            for (uid,) in self.db.query(ActivityLog.user_id)
            .filter(ActivityLog.user_id.isnot(None))
            .filter(ActivityLog.created_at >= since)
            .distinct()
            .all()
        }

        by_role = {
            "parent": 0, "child": 0, "teacher": 0, "admin": 0, "auditor": 0,
        }
        if active_ids:
            rows = (
                self.db.query(UserRole.user_id, Role.name)
                .join(Role, Role.id == UserRole.role_id)
                .filter(UserRole.user_id.in_(active_ids))
                .all()
            )
            counted: dict[str, set[str]] = defaultdict(set)
            for uid, role_name in rows:
                if role_name in by_role:
                    counted[role_name].add(uid)
            for k, ids in counted.items():
                by_role[k] = len(ids)

        return {
            "window_days": window_days,
            "since": since,
            "total_active": len(active_ids),
            "by_role": by_role,
        }

    # ---------------- activity overview ----------------

    def activity_overview(self, window_days: int) -> dict:
        since = datetime.utcnow() - timedelta(days=window_days)
        q = self.db.query(ActivityLog).filter(ActivityLog.created_at >= since)

        total = q.count()
        by_action_rows = (
            self.db.query(ActivityLog.action, func.count(ActivityLog.id))
            .filter(ActivityLog.created_at >= since)
            .group_by(ActivityLog.action)
            .order_by(func.count(ActivityLog.id).desc(), ActivityLog.action.asc())
            .all()
        )
        by_action = [{"action": a, "count": c} for a, c in by_action_rows]

        # by-day aggregation in Python: DB-portable across SQLite/MySQL.
        by_day_map: dict[str, int] = defaultdict(int)
        for row in q.with_entities(ActivityLog.created_at).all():
            d = row[0].date().isoformat()
            by_day_map[d] += 1
        by_day = [
            {"date": d, "count": c}
            for d, c in sorted(by_day_map.items())
        ]

        return {
            "window_days": window_days,
            "since": since,
            "total_events": total,
            "by_action": by_action,
            "by_day": by_day,
        }

    # ---------------- group progress ----------------

    def _ensure_group_visible(self, group: Group, user: User) -> None:
        roles = _user_roles(self.db, user.id)
        if roles & {"admin", "auditor"}:
            return
        if "teacher" in roles:
            tp = (
                self.db.query(TeacherProfile)
                .filter(TeacherProfile.user_id == user.id)
                .first()
            )
            if tp and group.teacher_id == tp.id:
                return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "group not accessible")

    def group_progress(self, group_id: str, user: User) -> dict:
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        self._ensure_group_visible(group, user)

        member_ids = [
            cid for (cid,) in self.db.query(GroupMember.child_id)
            .filter(GroupMember.group_id == group_id)
            .all()
        ]
        member_count = len(member_ids)

        prog_rows = (
            self.db.query(Programme)
            .join(GroupProgramme, GroupProgramme.programme_id == Programme.id)
            .filter(GroupProgramme.group_id == group_id)
            .all()
        )

        programmes_summary = []
        for prog in prog_rows:
            module_ids = [
                mid for (mid,) in self.db.query(Module.id)
                .filter(Module.programme_id == prog.id)
                .all()
            ]
            modules_total = len(module_ids)
            modules_completed_total = 0
            avg_pct = 0.0
            if member_ids and module_ids:
                completed_per_child: dict[str, int] = defaultdict(int)
                rows = (
                    self.db.query(ModuleProgress.child_id)
                    .filter(
                        ModuleProgress.child_id.in_(member_ids),
                        ModuleProgress.module_id.in_(module_ids),
                        ModuleProgress.status == "completed",
                    )
                    .all()
                )
                for (cid,) in rows:
                    completed_per_child[cid] += 1
                modules_completed_total = sum(completed_per_child.values())
                avg_pct = (
                    sum(
                        completed_per_child.get(cid, 0) / modules_total * 100.0
                        for cid in member_ids
                    )
                    / member_count
                )
            programmes_summary.append(
                {
                    "programme_id": prog.id,
                    "programme_name": prog.name,
                    "modules_total": modules_total,
                    "modules_completed_total": modules_completed_total,
                    "completion_avg_pct": round(avg_pct, 2),
                }
            )

        return {
            "group_id": group_id,
            "member_count": member_count,
            "programmes": programmes_summary,
        }

    # ---------------- programme funnel ----------------

    def _ensure_programme_visible(self, programme: Programme, user: User) -> None:
        roles = _user_roles(self.db, user.id)
        if roles & {"admin", "auditor"}:
            return
        if "teacher" in roles:
            tp = (
                self.db.query(TeacherProfile)
                .filter(TeacherProfile.user_id == user.id)
                .first()
            )
            if tp is None:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "programme not accessible")
            exists = (
                self.db.query(GroupProgramme)
                .join(Group, Group.id == GroupProgramme.group_id)
                .filter(
                    GroupProgramme.programme_id == programme.id,
                    Group.teacher_id == tp.id,
                )
                .first()
            )
            if exists:
                return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "programme not accessible")

    def programme_funnel(self, programme_id: str, user: User) -> dict:
        programme = (
            self.db.query(Programme).filter(Programme.id == programme_id).first()
        )
        if not programme:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
        self._ensure_programme_visible(programme, user)

        modules = (
            self.db.query(Module)
            .filter(Module.programme_id == programme_id)
            .order_by(Module.order_index.asc())
            .all()
        )

        # Children eligible = distinct children whose group has this programme assigned.
        child_ids = {
            cid for (cid,) in self.db.query(GroupMember.child_id)
            .join(GroupProgramme, GroupProgramme.group_id == GroupMember.group_id)
            .filter(GroupProgramme.programme_id == programme_id)
            .distinct()
            .all()
        }

        modules_summary = []
        for m in modules:
            started = 0
            completed = 0
            if child_ids:
                rows = (
                    self.db.query(ModuleProgress.status)
                    .filter(
                        ModuleProgress.module_id == m.id,
                        ModuleProgress.child_id.in_(child_ids),
                    )
                    .all()
                )
                for (status_val,) in rows:
                    if status_val in ("in_progress", "completed"):
                        started += 1
                    if status_val == "completed":
                        completed += 1
            modules_summary.append(
                {
                    "module_id": m.id,
                    "title": m.title,
                    "order_index": m.order_index,
                    "started": started,
                    "completed": completed,
                }
            )

        return {
            "programme_id": programme_id,
            "total_children": len(child_ids),
            "modules": modules_summary,
        }

    # ---------------- parent dashboard ----------------

    def child_dashboard(self, child_id: str, user: User) -> dict:
        roles = _user_roles(self.db, user.id)
        if "parent" not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "parent role required")
        parent = (
            self.db.query(ParentProfile)
            .filter(ParentProfile.user_id == user.id)
            .first()
        )
        if not parent:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "parent profile missing")

        link = (
            self.db.query(ParentChildRelation)
            .filter(
                ParentChildRelation.parent_id == parent.id,
                ParentChildRelation.child_id == child_id,
            )
            .first()
        )
        if not link:
            # Do not reveal whether the child exists at all.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "child not found")

        # Programmes assigned to any group the child is in.
        programmes = (
            self.db.query(Programme)
            .join(GroupProgramme, GroupProgramme.programme_id == Programme.id)
            .join(GroupMember, GroupMember.group_id == GroupProgramme.group_id)
            .filter(GroupMember.child_id == child_id)
            .distinct()
            .all()
        )

        out_programmes = []
        for prog in programmes:
            modules = (
                self.db.query(Module)
                .filter(Module.programme_id == prog.id)
                .order_by(Module.order_index.asc())
                .all()
            )
            module_summaries = []
            for m in modules:
                lesson_ids = [
                    lid for (lid,) in self.db.query(Lesson.id)
                    .filter(Lesson.module_id == m.id)
                    .all()
                ]
                lessons_total = len(lesson_ids)
                lessons_completed = 0
                if lesson_ids:
                    lessons_completed = (
                        self.db.query(func.count(LessonProgress.id))
                        .filter(
                            LessonProgress.child_id == child_id,
                            LessonProgress.lesson_id.in_(lesson_ids),
                            LessonProgress.status == "completed",
                        )
                        .scalar()
                    ) or 0
                mp = (
                    self.db.query(ModuleProgress.status)
                    .filter(
                        ModuleProgress.child_id == child_id,
                        ModuleProgress.module_id == m.id,
                    )
                    .first()
                )
                status_val = mp[0] if mp else "not_started"
                module_summaries.append(
                    {
                        "module_id": m.id,
                        "title": m.title,
                        "order_index": m.order_index,
                        "status": status_val,
                        "lessons_total": lessons_total,
                        "lessons_completed": lessons_completed,
                    }
                )
            out_programmes.append(
                {
                    "programme_id": prog.id,
                    "name": prog.name,
                    "modules": module_summaries,
                }
            )

        return {"child_id": child_id, "programmes": out_programmes}
