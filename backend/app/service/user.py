"""Service layer for /users/me — profile read, GDPR export, soft-delete with cascade."""
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.model.consent import Consent
from app.model.profile import ChildProfile
from app.model.user import RefreshToken, User
from app.repository.profile import ChildRepository, ParentRepository
from app.repository.user import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.parents = ParentRepository(db)
        self.children = ChildRepository(db)

    def get_me(self, user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "status": user.status,
            "roles": self.users.list_roles(user.id),
            "created_at": user.created_at,
        }

    def patch_me(self, user: User, _payload: dict) -> dict[str, Any]:
        # No user-level fields are mutable in MVP. Profile fields live under
        # /children/{id}, /parents/me, /teachers/me.
        return self.get_me(user)

    def export_me(self, user: User) -> dict[str, Any]:
        """GDPR Art. 15 export. Excludes password_hash and refresh_tokens."""
        data: dict[str, Any] = {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "status": user.status,
                "last_login_at": _iso(user.last_login_at),
                "created_at": _iso(user.created_at),
                "deleted_at": _iso(user.deleted_at),
                "roles": self.users.list_roles(user.id),
            },
            "profile": None,
            "children": [],
            "consents": [],
            "activity_summary": [],
        }

        parent = self.parents.get_by_user_id(user.id)
        if parent:
            data["profile"] = {"type": "parent", "id": parent.id}
            for child in self.parents.list_children(parent.id):
                data["children"].append(_child_dict(child))
            data["consents"] = [
                _consent_dict(c)
                for c in self.db.query(Consent).filter(Consent.parent_id == parent.id).all()
            ]

        child = self.children.get_by_user_id(user.id)
        if child:
            data["profile"] = {"type": "child", **_child_dict(child)}

        return data

    def delete_me(self, user: User) -> None:
        """Soft-delete the user; for parents, cascade to linked children."""
        now = datetime.utcnow()
        affected_user_ids: list[str] = [user.id]

        parent = self.parents.get_by_user_id(user.id)
        if parent:
            for child in self.parents.list_children(parent.id):
                child.deleted_at = now
                child_user = (
                    self.users.get_by_id(child.user_id) if child.user_id else None
                )
                if child_user and child_user.deleted_at is None:
                    child_user.deleted_at = now
                    child_user.status = "disabled"
                    affected_user_ids.append(child_user.id)

        user.deleted_at = now
        user.status = "disabled"

        self.db.query(RefreshToken).filter(
            RefreshToken.user_id.in_(affected_user_ids),
            RefreshToken.revoked_at.is_(None),
        ).update({RefreshToken.revoked_at: now}, synchronize_session=False)
        self.db.commit()


def _iso(dt):
    return dt.isoformat() if dt else None


def _child_dict(child: ChildProfile) -> dict[str, Any]:
    return {
        "id": child.id,
        "user_id": child.user_id,
        "first_name": child.first_name,
        "last_name": child.last_name,
        "date_of_birth": child.date_of_birth.isoformat() if child.date_of_birth else None,
        "native_language": child.native_language,
        "school_id": child.school_id,
        "deleted_at": _iso(child.deleted_at),
    }


def _consent_dict(c: Consent) -> dict[str, Any]:
    return {
        "id": c.id,
        "parent_id": c.parent_id,
        "child_id": c.child_id,
        "consent_type": c.consent_type,
        "consent_version": c.consent_version,
        "granted_at": _iso(c.granted_at),
        "revoked_at": _iso(c.revoked_at),
    }