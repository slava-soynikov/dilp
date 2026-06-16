"""Service for /consents. Grant/revoke flips the linked child's status."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.model.consent import Consent
from app.model.profile import ParentChildRelation
from app.model.user import User
from app.repository.consent import ConsentRepository
from app.repository.profile import ChildRepository, ParentRepository
from app.repository.user import UserRepository


class ConsentService:
    def __init__(self, db: Session):
        self.db = db
        self.consents = ConsentRepository(db)
        self.parents = ParentRepository(db)
        self.children = ChildRepository(db)
        self.users = UserRepository(db)

    def list_for_parent(self, parent_user: User) -> list[Consent]:
        parent = self.parents.get_by_user_id(parent_user.id)
        if not parent:
            return []
        return (
            self.db.query(Consent)
            .filter(Consent.parent_id == parent.id)
            .order_by(Consent.granted_at.desc())
            .all()
        )

    def grant(self, parent_user: User, child_id: str, consent_type: str,
              consent_version: str, consent_text_ref: str | None) -> Consent:
        parent = self.parents.get_by_user_id(parent_user.id)
        if not parent:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "not a parent")
        if not self._parent_owns_child(parent.id, child_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "child not found")

        c = self.consents.create(
            parent.id, child_id, consent_type, consent_version, consent_text_ref
        )
        self._sync_child_status(child_id)
        self.db.commit()
        return c

    def revoke(self, parent_user: User, consent_id: str) -> Consent:
        c = self.consents.get_by_id(consent_id)
        if not c:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "consent not found")
        parent = self.parents.get_by_user_id(parent_user.id)
        if not parent or c.parent_id != parent.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "consent not found")
        if c.revoked_at is None:
            self.consents.revoke(c)
            self._sync_child_status(c.child_id)
        self.db.commit()
        return c

    def _parent_owns_child(self, parent_id: str, child_id: str) -> bool:
        return (
            self.db.query(ParentChildRelation)
            .filter_by(parent_id=parent_id, child_id=child_id)
            .count()
            > 0
        )

    def _sync_child_status(self, child_id: str) -> None:
        """data_processing consent gates child user activation (architecture §7.2)."""
        child = self.children.get_by_id(child_id)
        if not child or not child.user_id:
            return
        child_user = self.users.get_by_id(child.user_id)
        if not child_user:
            return
        has_dp = self.consents.has_active(child_id, "data_processing")
        target = "active" if has_dp else "pending"
        if child_user.status != target:
            child_user.status = target
            self.db.flush()