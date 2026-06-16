import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class ActivityLog(Base):
    """Behavioral log: what users did (login, lesson_open, module_start, ...)."""
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(255), nullable=True)  # generic — composite PKs serialize to >36 chars
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        Index("ix_activity_logs_user_created", "user_id", "created_at"),
        Index("ix_activity_logs_entity", "entity_type", "entity_id"),
    )


class AuditLog(Base):
    """Compliance log: who changed what (data mutations on sensitive tables)."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # create | update | delete
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=False)
    diff = Column(Text, nullable=True)  # JSON-encoded before/after
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
    )