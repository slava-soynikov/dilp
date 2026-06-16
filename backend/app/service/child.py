"""Service for /children — parent-driven creation of pending child accounts."""
import secrets
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.model.profile import ChildProfile, ParentChildRelation
from app.model.user import Role, User, UserRole
from app.repository.profile import ParentRepository
from app.repository.user import UserRepository


def generate_pin() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(8))


class ChildService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.parents = ParentRepository(db)

    def create_for_parent(self, parent_user: User, payload: dict[str, Any]) -> dict[str, Any]:
        parent = self.parents.get_by_user_id(parent_user.id)
        if not parent:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not a parent")

        username = payload["username"]
        if self.users.get_by_username(username):
            raise HTTPException(status.HTTP_409_CONFLICT, "username already taken")

        pin = generate_pin()
        child_user = User(
            username=username,
            email=None,
            password_hash=hash_password(pin),
            status="pending",
        )
        self.db.add(child_user)
        self.db.flush()

        child_role = self.db.query(Role).filter_by(name="child").one()
        self.db.add(UserRole(user_id=child_user.id, role_id=child_role.id))

        child = ChildProfile(
            user_id=child_user.id,
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            date_of_birth=payload.get("date_of_birth"),
            native_language=payload.get("native_language"),
            school_id=payload.get("school_id"),
        )
        self.db.add(child)
        self.db.flush()

        self.db.add(ParentChildRelation(parent_id=parent.id, child_id=child.id))
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "username already taken")

        return {
            "id": child.id,
            "user_id": child.user_id,
            "username": child_user.username,
            "status": child_user.status,
            "first_name": child.first_name,
            "last_name": child.last_name,
            "date_of_birth": child.date_of_birth,
            "native_language": child.native_language,
            "school_id": child.school_id,
            "pin": pin,
        }

    def patch(self, parent_user: User, child_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        parent = self.parents.get_by_user_id(parent_user.id)
        if not parent:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not a parent")
        from app.model.profile import ParentChildRelation

        rel = (
            self.db.query(ParentChildRelation)
            .filter_by(parent_id=parent.id, child_id=child_id)
            .first()
        )
        if not rel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "child not found")
        from app.repository.profile import ChildRepository
        child = ChildRepository(self.db).get_by_id(child_id)
        if not child:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "child not found")

        for field in ("first_name", "last_name", "date_of_birth", "native_language"):
            if field in payload and payload[field] is not None:
                setattr(child, field, payload[field])
        self.db.commit()
        child_user = self.users.get_by_id(child.user_id) if child.user_id else None
        return {
            "id": child.id,
            "user_id": child.user_id,
            "username": child_user.username if child_user else None,
            "status": child_user.status if child_user else None,
            "first_name": child.first_name,
            "last_name": child.last_name,
            "date_of_birth": child.date_of_birth,
            "native_language": child.native_language,
            "school_id": child.school_id,
        }

    def list_for_parent(self, parent_user: User) -> list[dict[str, Any]]:
        parent = self.parents.get_by_user_id(parent_user.id)
        if not parent:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not a parent")
        result = []
        for child in self.parents.list_children(parent.id):
            child_user = self.users.get_by_id(child.user_id) if child.user_id else None
            result.append({
                "id": child.id,
                "user_id": child.user_id,
                "username": child_user.username if child_user else None,
                "status": child_user.status if child_user else None,
                "first_name": child.first_name,
                "last_name": child.last_name,
                "date_of_birth": child.date_of_birth,
                "native_language": child.native_language,
                "school_id": child.school_id,
            })
        return result