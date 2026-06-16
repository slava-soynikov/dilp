import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = Column(String(36), ForeignKey("child_profiles.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="not_started")  # not_started | in_progress | completed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    child = relationship("ChildProfile", back_populates="module_progress")
    module = relationship("Module", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("child_id", "module_id", name="uq_module_progress_child_module"),
        Index("ix_module_progress_child_id", "child_id"),
    )


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = Column(String(36), ForeignKey("child_profiles.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="not_started")  # not_started | in_progress | completed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    child = relationship("ChildProfile", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("child_id", "lesson_id", name="uq_lesson_progress_child_lesson"),
        Index("ix_lesson_progress_child_id", "child_id"),
    )