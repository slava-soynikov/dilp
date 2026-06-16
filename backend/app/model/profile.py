import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class ChildProfile(Base):
    __tablename__ = "child_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    native_language = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # GDPR soft-delete

    user = relationship("User", back_populates="child_profile")
    school = relationship("School", back_populates="children")
    parent_relations = relationship("ParentChildRelation", back_populates="child", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="child", cascade="all, delete-orphan")
    module_progress = relationship("ModuleProgress", back_populates="child", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="child", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="child")

    __table_args__ = (
        Index("ix_child_profiles_school_id", "school_id"),
    )


class ParentProfile(Base):
    __tablename__ = "parent_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="parent_profile")
    child_relations = relationship("ParentChildRelation", back_populates="parent", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="parent")


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="teacher_profile")
    groups = relationship("Group", back_populates="teacher")


class ParentChildRelation(Base):
    __tablename__ = "parent_child_relations"

    parent_id = Column(String(36), ForeignKey("parent_profiles.id", ondelete="CASCADE"), primary_key=True)
    child_id = Column(String(36), ForeignKey("child_profiles.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    parent = relationship("ParentProfile", back_populates="child_relations")
    child = relationship("ChildProfile", back_populates="parent_relations")

    __table_args__ = (
        Index("ix_pcr_child_id", "child_id"),
    )