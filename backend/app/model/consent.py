import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("parent_profiles.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(String(36), ForeignKey("child_profiles.id", ondelete="CASCADE"), nullable=False)
    consent_type = Column(String(100), nullable=False)  # data_processing | content_access | ...
    consent_version = Column(String(20), nullable=False, default="1.0")
    consent_text_ref = Column(String(500), nullable=True)  # link/ref to the legal text granted
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)  # GDPR Art. 7(3) — right to withdraw

    parent = relationship("ParentProfile", back_populates="consents")
    child = relationship("ChildProfile", back_populates="consents")

    __table_args__ = (
        Index("ix_consents_child_type", "child_id", "consent_type"),
        Index("ix_consents_parent_id", "parent_id"),
    )