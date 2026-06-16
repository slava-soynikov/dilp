import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)  # null = global
    name = Column(String(255), nullable=False)
    language = Column(String(10), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="programmes")
    modules = relationship(
        "Module",
        back_populates="programme",
        order_by="Module.order_index",
        cascade="all, delete-orphan",
    )
    group_assignments = relationship(
        "GroupProgramme",
        back_populates="programme",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_programmes_tenant_id", "tenant_id"),
    )


class Module(Base):
    __tablename__ = "modules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    programme_id = Column(String(36), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    programme = relationship("Programme", back_populates="modules")
    lessons = relationship(
        "Lesson",
        back_populates="module",
        order_by="Lesson.order_index",
        cascade="all, delete-orphan",
    )
    progress = relationship("ModuleProgress", back_populates="module", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("programme_id", "order_index", name="uq_modules_programme_order"),
        Index("ix_modules_programme_id", "programme_id"),
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content_ref = Column(String(500))  # CMS reference (path appended to CMS_BASE_URL)
    meeting_url = Column(String(2048), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    module = relationship("Module", back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("module_id", "order_index", name="uq_lessons_module_order"),
        Index("ix_lessons_module_id", "module_id"),
    )