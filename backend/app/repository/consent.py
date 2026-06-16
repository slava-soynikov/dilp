from datetime import datetime

from sqlalchemy.orm import Session

from app.model.consent import Consent


class ConsentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        parent_id: str,
        child_id: str,
        consent_type: str,
        consent_version: str = "1.0",
        consent_text_ref: str | None = None,
    ) -> Consent:
        c = Consent(
            parent_id=parent_id,
            child_id=child_id,
            consent_type=consent_type,
            consent_version=consent_version,
            consent_text_ref=consent_text_ref,
        )
        self.db.add(c)
        self.db.flush()
        return c

    def get_by_id(self, consent_id: str) -> Consent | None:
        return self.db.query(Consent).filter(Consent.id == consent_id).first()

    def has_active(self, child_id: str, consent_type: str) -> bool:
        return (
            self.db.query(Consent)
            .filter(
                Consent.child_id == child_id,
                Consent.consent_type == consent_type,
                Consent.revoked_at.is_(None),
            )
            .count()
            > 0
        )

    def revoke(self, c: Consent) -> None:
        c.revoked_at = datetime.utcnow()
        self.db.flush()