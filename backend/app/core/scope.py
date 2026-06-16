"""RBAC scoping helper. Resolves the set of tenant/school/group/child IDs a
user is allowed to access, based on their roles.
"""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.model.group import Group, GroupMember
from app.model.profile import (
    ChildProfile,
    ParentChildRelation,
    ParentProfile,
    TeacherProfile,
)
from app.model.user import User
from app.repository.user import UserRepository


@dataclass
class AccessScope:
    is_admin: bool = False
    tenant_ids: set[str] = field(default_factory=set)
    school_ids: set[str] = field(default_factory=set)
    group_ids: set[str] = field(default_factory=set)
    child_ids: set[str] = field(default_factory=set)

    def can_see_school(self, school_id: str) -> bool:
        return self.is_admin or school_id in self.school_ids

    def can_see_group(self, group_id: str) -> bool:
        return self.is_admin or group_id in self.group_ids

    def can_see_child(self, child_id: str) -> bool:
        return self.is_admin or child_id in self.child_ids


def resolve_scope(db: Session, user: User) -> AccessScope:
    roles = set(UserRepository(db).list_roles(user.id))
    scope = AccessScope()
    if "admin" in roles:
        scope.is_admin = True
        return scope

    if "parent" in roles:
        parent = (
            db.query(ParentProfile).filter(ParentProfile.user_id == user.id).first()
        )
        if parent:
            child_rows = (
                db.query(ChildProfile.id, ChildProfile.school_id)
                .join(ParentChildRelation, ParentChildRelation.child_id == ChildProfile.id)
                .filter(
                    ParentChildRelation.parent_id == parent.id,
                    ChildProfile.deleted_at.is_(None),
                )
                .all()
            )
            for cid, sid in child_rows:
                scope.child_ids.add(cid)
                if sid:
                    scope.school_ids.add(sid)
            if scope.child_ids:
                group_rows = (
                    db.query(GroupMember.group_id)
                    .filter(GroupMember.child_id.in_(scope.child_ids))
                    .all()
                )
                scope.group_ids.update(g[0] for g in group_rows)

    if "teacher" in roles:
        teacher = (
            db.query(TeacherProfile).filter(TeacherProfile.user_id == user.id).first()
        )
        if teacher:
            group_rows = (
                db.query(Group.id, Group.school_id)
                .filter(Group.teacher_id == teacher.id)
                .all()
            )
            for gid, sid in group_rows:
                scope.group_ids.add(gid)
                scope.school_ids.add(sid)
            if scope.group_ids:
                child_rows = (
                    db.query(GroupMember.child_id)
                    .filter(GroupMember.group_id.in_(scope.group_ids))
                    .all()
                )
                scope.child_ids.update(c[0] for c in child_rows)

    if "child" in roles:
        child = (
            db.query(ChildProfile).filter(ChildProfile.user_id == user.id).first()
        )
        if child:
            scope.child_ids.add(child.id)
            if child.school_id:
                scope.school_ids.add(child.school_id)

    return scope
