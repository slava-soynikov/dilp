"""Progress tracking service (Sprint 5).

Architecture references:
- §5.1 / §7.3: Child writes own progress only; access strictly to assigned curriculum.
- §6.2: Platform Core owns progress as system of record (CMS stays content-only).

Authorization model:
- Only users with the ``child`` role and an active ChildProfile may write progress.
- A child may write progress for a module/lesson only if its programme is assigned
  (via ``group_programmes``) to one of the child's groups (§7.3 "Child: eigene
  Lerninhalte"). Otherwise the resource is treated as not found.
- ``module/complete`` is a manual override; the canonical flow auto-completes the
  parent module when the last lesson in it transitions to ``completed``.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.model.group import GroupMember, GroupProgramme
from app.model.profile import ChildProfile
from app.model.programme import Lesson, Module
from app.model.progress import LessonProgress, ModuleProgress
from app.model.user import User
from app.repository.progress import (
    LessonProgressRepository,
    ModuleProgressRepository,
)
from app.repository.user import UserRepository


def _require_child(db: Session, user: User) -> ChildProfile:
    roles = set(UserRepository(db).list_roles(user.id))
    if "child" not in roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "child role required")
    # Architecture §7.2: progress writes require active parental consent. The
    # consent service flips child user.status to "pending" on revoke, but
    # short-lived access tokens issued before revocation would otherwise keep
    # working. Re-check per request.
    if user.status != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent required")
    profile = (
        db.query(ChildProfile).filter(ChildProfile.user_id == user.id).first()
    )
    if not profile:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "child profile missing")
    return profile


def _child_programme_ids(db: Session, child_id: str) -> set[str]:
    rows = (
        db.query(GroupProgramme.programme_id)
        .join(GroupMember, GroupMember.group_id == GroupProgramme.group_id)
        .filter(GroupMember.child_id == child_id)
        .all()
    )
    return {r[0] for r in rows}


class ProgressService:
    def __init__(self, db: Session):
        self.db = db
        self.modules = ModuleProgressRepository(db)
        self.lessons = LessonProgressRepository(db)

    # ---------------- helpers ----------------

    def _load_module_for_child(
        self, child: ChildProfile, module_id: str
    ) -> Module:
        module = self.db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "module not found")
        if module.programme_id not in _child_programme_ids(self.db, child.id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "module not found")
        return module

    def _load_lesson_for_child(
        self, child: ChildProfile, lesson_id: str
    ) -> tuple[Lesson, Module]:
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson not found")
        module = self.db.query(Module).filter(Module.id == lesson.module_id).first()
        if not module or module.programme_id not in _child_programme_ids(
            self.db, child.id
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson not found")
        return lesson, module

    def _get_or_create_module_progress(
        self, child_id: str, module_id: str
    ) -> ModuleProgress:
        mp = self.modules.get(child_id, module_id)
        if mp is None:
            mp = self.modules.create(child_id, module_id)
        return mp

    def _get_or_create_lesson_progress(
        self, child_id: str, lesson_id: str
    ) -> LessonProgress:
        lp = self.lessons.get(child_id, lesson_id)
        if lp is None:
            lp = self.lessons.create(child_id, lesson_id)
        return lp

    def _maybe_autocomplete_module(self, child_id: str, module: Module) -> None:
        lesson_ids = [l.id for l in module.lessons]
        if not lesson_ids:
            return
        rows = self.lessons.list_for_module(child_id, lesson_ids)
        if len(rows) < len(lesson_ids):
            return
        if not all(r.status == "completed" for r in rows):
            return
        mp = self._get_or_create_module_progress(child_id, module.id)
        now = datetime.utcnow()
        if mp.started_at is None:
            mp.started_at = now
        mp.status = "completed"
        mp.completed_at = now

    # ---------------- module endpoints ----------------

    def start_module(self, user: User, module_id: str) -> ModuleProgress:
        child = _require_child(self.db, user)
        module = self._load_module_for_child(child, module_id)
        mp = self._get_or_create_module_progress(child.id, module.id)
        if mp.status == "not_started":
            mp.status = "in_progress"
            mp.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(mp)
        return mp

    def complete_module(self, user: User, module_id: str) -> ModuleProgress:
        child = _require_child(self.db, user)
        module = self._load_module_for_child(child, module_id)
        mp = self._get_or_create_module_progress(child.id, module.id)
        now = datetime.utcnow()
        if mp.started_at is None:
            mp.started_at = now
        mp.status = "completed"
        mp.completed_at = now
        self.db.commit()
        self.db.refresh(mp)
        return mp

    # ---------------- lesson endpoints ----------------

    def start_lesson(self, user: User, lesson_id: str) -> LessonProgress:
        child = _require_child(self.db, user)
        lesson, module = self._load_lesson_for_child(child, lesson_id)
        lp = self._get_or_create_lesson_progress(child.id, lesson.id)
        now = datetime.utcnow()
        if lp.status == "not_started":
            lp.status = "in_progress"
            lp.started_at = now
        lp.last_accessed_at = now
        # mirror onto module: in_progress as soon as any lesson is touched
        mp = self._get_or_create_module_progress(child.id, module.id)
        if mp.status == "not_started":
            mp.status = "in_progress"
            mp.started_at = now
        self.db.commit()
        self.db.refresh(lp)
        return lp

    def complete_lesson(self, user: User, lesson_id: str) -> LessonProgress:
        child = _require_child(self.db, user)
        lesson, module = self._load_lesson_for_child(child, lesson_id)
        lp = self._get_or_create_lesson_progress(child.id, lesson.id)
        now = datetime.utcnow()
        if lp.started_at is None:
            lp.started_at = now
        lp.status = "completed"
        lp.completed_at = now
        lp.last_accessed_at = now
        # ensure module shows in_progress for the parent before potential autocomplete
        mp = self._get_or_create_module_progress(child.id, module.id)
        if mp.status == "not_started":
            mp.status = "in_progress"
            mp.started_at = now
        self._maybe_autocomplete_module(child.id, module)
        self.db.commit()
        self.db.refresh(lp)
        return lp

    def heartbeat_lesson(self, user: User, lesson_id: str) -> LessonProgress:
        child = _require_child(self.db, user)
        lesson, module = self._load_lesson_for_child(child, lesson_id)
        lp = self._get_or_create_lesson_progress(child.id, lesson.id)
        now = datetime.utcnow()
        if lp.status == "not_started":
            lp.status = "in_progress"
            lp.started_at = now
        lp.last_accessed_at = now
        mp = self._get_or_create_module_progress(child.id, module.id)
        if mp.status == "not_started":
            mp.status = "in_progress"
            mp.started_at = now
        self.db.commit()
        self.db.refresh(lp)
        return lp