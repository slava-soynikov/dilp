"""Group + GroupMember services with RBAC scoping.

Per locked Sprint 3 decisions:
- Admin creates groups; teacher cannot.
- Admin OR the group's own teacher can add/remove members.
- Adding a child whose school differs from the group's school is rejected (409).
- A child without school inherits the group's school on first membership.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.scope import resolve_scope
from app.model.group import Group, GroupMember
from app.model.profile import ChildProfile, TeacherProfile
from app.model.tenant import School
from app.model.user import Role, User, UserRole
from app.repository.group import GroupMemberRepository, GroupRepository
from app.repository.tenant import SchoolRepository


class GroupService:
    def __init__(self, db: Session):
        self.db = db
        self.groups = GroupRepository(db)
        self.members = GroupMemberRepository(db)
        self.schools = SchoolRepository(db)

    def list_for_user(self, user: User) -> list[Group]:
        scope = resolve_scope(self.db, user)
        if scope.is_admin:
            return self.groups.list_all()
        return self.groups.list_by_ids(scope.group_ids)

    def create(self, school_id: str, teacher_id: str, name: str) -> Group:
        if not self.schools.get_by_id(school_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "school not found")
        if not self.db.query(TeacherProfile).filter_by(id=teacher_id).first():
            raise HTTPException(status.HTTP_404_NOT_FOUND, "teacher not found")
        g = self.groups.create(school_id, teacher_id, name)
        self.db.commit()
        return g

    def patch(self, user: User, group_id: str, payload: dict) -> Group:
        g = self.groups.get_by_id(group_id)
        if not g:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        scope = resolve_scope(self.db, user)
        if not scope.can_see_group(g.id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        if "name" in payload and payload["name"] is not None:
            g.name = payload["name"]
        self.db.commit()
        return g

    def delete(self, group_id: str) -> None:
        g = self.groups.get_by_id(group_id)
        if not g:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        self.groups.delete(g)
        self.db.commit()

    # ----- members -----

    def _group_for_member_ops(self, user: User, group_id: str) -> Group:
        """Admin: any group. Teacher: only own groups. Otherwise 404."""
        is_admin = (
            self.db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id, Role.name == "admin")
            .first()
            is not None
        )
        g = self.groups.get_by_id(group_id)
        if not g:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        if is_admin:
            return g
        teacher = (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == user.id)
            .first()
        )
        if not teacher or g.teacher_id != teacher.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        return g

    def add_member(self, user: User, group_id: str, child_id: str) -> GroupMember:
        g = self._group_for_member_ops(user, group_id)
        child = (
            self.db.query(ChildProfile)
            .filter(ChildProfile.id == child_id, ChildProfile.deleted_at.is_(None))
            .first()
        )
        if not child:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "child not found")

        if child.school_id and child.school_id != g.school_id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "child belongs to a different school",
            )
        if child.school_id is None:
            child.school_id = g.school_id

        existing = self.members.get(group_id, child_id)
        if existing:
            return existing
        m = self.members.add(group_id, child_id)
        self.db.commit()
        return m

    def remove_member(self, user: User, group_id: str, child_id: str) -> None:
        self._group_for_member_ops(user, group_id)
        m = self.members.get(group_id, child_id)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "member not found")
        self.members.remove(m)
        self.db.commit()

    def list_members(self, user: User, group_id: str) -> list[ChildProfile]:
        g = self.groups.get_by_id(group_id)
        if not g:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        scope = resolve_scope(self.db, user)
        if not scope.can_see_group(g.id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "group not found")
        child_ids = [m.child_id for m in self.members.list_by_group(group_id)]
        if not child_ids:
            return []
        return (
            self.db.query(ChildProfile)
            .filter(ChildProfile.id.in_(child_ids), ChildProfile.deleted_at.is_(None))
            .all()
        )