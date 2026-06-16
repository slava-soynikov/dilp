"""Programme/Module/Lesson services + group-programme assignment.

Authoring rules (Sprint 4 locked):
- Programme CRUD: admin only (enforced at the route via require_role).
- Module/Lesson CRUD: admin OR teacher whose group has the parent programme
  assigned. This ties §5.1 ("Teacher betreut Lernmodule") to §7.3 (RBAC
  scoped to assigned Lerngruppen).
- Programme visibility (list/get): admin sees all; everyone else sees
  tenant programmes (their tenants) + global (tenant_id IS NULL).
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.scope import resolve_scope
from app.integrations.cms import CMSClient, CMSError
from app.model.group import GroupProgramme
from app.model.profile import TeacherProfile
from app.model.programme import Lesson, Module, Programme
from app.model.tenant import School
from app.model.user import User
from app.repository.group import GroupRepository
from app.repository.programme import (
    GroupProgrammeRepository,
    LessonRepository,
    ModuleRepository,
    ProgrammeRepository,
)
from app.repository.tenant import TenantRepository
from app.repository.user import UserRepository


def _user_tenant_ids(db: Session, user: User) -> set[str]:
    scope = resolve_scope(db, user)
    if scope.is_admin or not scope.school_ids:
        return set()
    rows = (
        db.query(School.tenant_id).filter(School.id.in_(scope.school_ids)).all()
    )
    return {r[0] for r in rows}


def _user_assigned_programme_ids(db: Session, user: User) -> set[str]:
    """Programmes assigned to any of the user's groups."""
    scope = resolve_scope(db, user)
    if not scope.group_ids:
        return set()
    rows = (
        db.query(GroupProgramme.programme_id)
        .filter(GroupProgramme.group_id.in_(scope.group_ids))
        .all()
    )
    return {r[0] for r in rows}


def _is_admin(db: Session, user: User) -> bool:
    return "admin" in set(UserRepository(db).list_roles(user.id))


def _is_teacher(db: Session, user: User) -> bool:
    return "teacher" in set(UserRepository(db).list_roles(user.id))


def _can_see_programme(db: Session, user: User, p: Programme) -> bool:
    if _is_admin(db, user):
        return True
    if p.tenant_id is None:
        return True
    return p.tenant_id in _user_tenant_ids(db, user)


def _can_author_in_programme(db: Session, user: User, p: Programme) -> bool:
    if _is_admin(db, user):
        return True
    if not _is_teacher(db, user):
        return False
    return p.id in _user_assigned_programme_ids(db, user)


# ---------------- Programme ----------------


class ProgrammeService:
    def __init__(self, db: Session):
        self.db = db
        self.programmes = ProgrammeRepository(db)
        self.tenants = TenantRepository(db)

    def create(self, name: str, language: str, tenant_id: str | None) -> Programme:
        if tenant_id is not None and not self.tenants.get_by_id(tenant_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
        p = self.programmes.create(name=name, language=language, tenant_id=tenant_id)
        self.db.commit()
        return p

    def list_for_user(self, user: User) -> list[Programme]:
        if _is_admin(self.db, user):
            return self.programmes.list_all()
        return self.programmes.list_by_tenants_and_global(
            _user_tenant_ids(self.db, user)
        )

    def get_for_user(self, user: User, programme_id: str) -> Programme:
        p = self.programmes.get_by_id(programme_id)
        if not p or not _can_see_programme(self.db, user, p):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
        return p

    def patch(self, programme_id: str, payload: dict) -> Programme:
        p = self.programmes.get_by_id(programme_id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
        if "name" in payload and payload["name"] is not None:
            p.name = payload["name"]
        if "language" in payload and payload["language"] is not None:
            p.language = payload["language"]
        self.db.commit()
        return p

    def delete(self, programme_id: str) -> None:
        p = self.programmes.get_by_id(programme_id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
        self.programmes.delete(p)
        self.db.commit()


# ---------------- Module ----------------


class ModuleService:
    def __init__(self, db: Session):
        self.db = db
        self.modules = ModuleRepository(db)
        self.programmes = ProgrammeRepository(db)

    def _load_programme(self, programme_id: str) -> Programme:
        p = self.programmes.get_by_id(programme_id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
        return p

    def create(
        self, user: User, programme_id: str, title: str, order_index: int
    ) -> Module:
        p = self._load_programme(programme_id)
        if not _can_author_in_programme(self.db, user, p):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed")
        if self.modules.order_exists(programme_id, order_index):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "module order_index already used"
            )
        m = self.modules.create(programme_id, title, order_index)
        self.db.commit()
        return m

    def patch(self, user: User, module_id: str, payload: dict) -> Module:
        m = self.modules.get_by_id(module_id)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "module not found")
        p = self.programmes.get_by_id(m.programme_id)
        if not _can_author_in_programme(self.db, user, p):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed")
        if "title" in payload and payload["title"] is not None:
            m.title = payload["title"]
        if "order_index" in payload and payload["order_index"] is not None:
            new_idx = payload["order_index"]
            if new_idx != m.order_index and self.modules.order_exists(
                m.programme_id, new_idx
            ):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "module order_index already used"
                )
            m.order_index = new_idx
        self.db.commit()
        return m

    def delete(self, user: User, module_id: str) -> None:
        m = self.modules.get_by_id(module_id)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "module not found")
        p = self.programmes.get_by_id(m.programme_id)
        if not _can_author_in_programme(self.db, user, p):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed")
        self.modules.delete(m)
        self.db.commit()


# ---------------- Lesson ----------------


class LessonService:
    def __init__(self, db: Session):
        self.db = db
        self.lessons = LessonRepository(db)
        self.modules = ModuleRepository(db)
        self.programmes = ProgrammeRepository(db)

    def _programme_for_module(self, module_id: str) -> tuple[Module, Programme]:
        m = self.modules.get_by_id(module_id)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "module not found")
        p = self.programmes.get_by_id(m.programme_id)
        return m, p

    def create(
        self,
        user: User,
        module_id: str,
        title: str,
        content_ref: str | None,
        order_index: int,
        meeting_url: str | None = None,
    ) -> Lesson:
        m, p = self._programme_for_module(module_id)
        if not _can_author_in_programme(self.db, user, p):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed")
        if self.lessons.order_exists(module_id, order_index):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "lesson order_index already used"
            )
        l = self.lessons.create(
            module_id, title, content_ref, order_index, meeting_url=meeting_url
        )
        self.db.commit()
        return l

    def patch(self, user: User, lesson_id: str, payload: dict) -> Lesson:
        l = self.lessons.get_by_id(lesson_id)
        if not l:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson not found")
        m, p = self._programme_for_module(l.module_id)
        if not _can_author_in_programme(self.db, user, p):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed")
        if "title" in payload and payload["title"] is not None:
            l.title = payload["title"]
        if "content_ref" in payload:
            l.content_ref = payload["content_ref"]
        if "meeting_url" in payload:
            l.meeting_url = payload["meeting_url"]
        if "order_index" in payload and payload["order_index"] is not None:
            new_idx = payload["order_index"]
            if new_idx != l.order_index and self.lessons.order_exists(
                l.module_id, new_idx
            ):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "lesson order_index already used"
                )
            l.order_index = new_idx
        self.db.commit()
        return l

    def delete(self, user: User, lesson_id: str) -> None:
        l = self.lessons.get_by_id(lesson_id)
        if not l:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson not found")
        m, p = self._programme_for_module(l.module_id)
        if not _can_author_in_programme(self.db, user, p):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed")
        self.lessons.delete(l)
        self.db.commit()

    def get_with_content(
        self, user: User, lesson_id: str, cms: CMSClient
    ) -> tuple[Lesson, dict | None]:
        l = self.lessons.get_by_id(lesson_id)
        if not l:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson not found")
        m, p = self._programme_for_module(l.module_id)
        if not _can_see_programme(self.db, user, p):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson not found")
        content: dict | None = None
        if l.content_ref:
            try:
                content = cms.get_content(l.content_ref)
            except CMSError as exc:
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
        return l, content


# ---------------- Group ↔ Programme assignment ----------------


class GroupProgrammeService:
    """Assigns programmes to a group. Teacher of the group or admin."""

    def __init__(self, db: Session):
        self.db = db
        self.groups = GroupRepository(db)
        self.programmes = ProgrammeRepository(db)
        self.assignments = GroupProgrammeRepository(db)

    def _authorize_group(self, user: User, group_id: str):
        g = self.groups.get_by_id(group_id)
        if not g:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        if _is_admin(self.db, user):
            return g
        teacher = (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == user.id)
            .first()
        )
        if not teacher or g.teacher_id != teacher.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        return g

    def assign(self, user: User, group_id: str, programme_id: str) -> GroupProgramme:
        self._authorize_group(user, group_id)
        if not self.programmes.get_by_id(programme_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
        existing = self.assignments.get(group_id, programme_id)
        if existing:
            return existing
        gp = self.assignments.add(group_id, programme_id)
        self.db.commit()
        return gp

    def list_for_group(self, user: User, group_id: str) -> list[GroupProgramme]:
        self._authorize_group(user, group_id)
        return (
            self.db.query(GroupProgramme)
            .filter(GroupProgramme.group_id == group_id)
            .all()
        )

    def unassign(self, user: User, group_id: str, programme_id: str) -> None:
        self._authorize_group(user, group_id)
        gp = self.assignments.get(group_id, programme_id)
        if not gp:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "assignment not found")
        self.assignments.remove(gp)
        self.db.commit()


# ---------------- Curriculum (child-facing) ----------------


class CurriculumService:
    def __init__(self, db: Session):
        self.db = db
        self.programmes = ProgrammeRepository(db)
        self.assignments = GroupProgrammeRepository(db)

    def for_child(self, user: User) -> list[Programme]:
        from app.model.group import GroupMember
        from app.model.profile import ChildProfile

        child = (
            self.db.query(ChildProfile)
            .filter(ChildProfile.user_id == user.id)
            .first()
        )
        if not child:
            return []
        group_rows = (
            self.db.query(GroupMember.group_id)
            .filter(GroupMember.child_id == child.id)
            .all()
        )
        group_ids = {r[0] for r in group_rows}
        if not group_ids:
            return []
        programme_ids = self.assignments.list_programme_ids_by_groups(group_ids)
        if not programme_ids:
            return []
        return self.programmes.list_by_ids(programme_ids)
