import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    school = relationship("School", back_populates="groups")
    teacher = relationship("TeacherProfile", back_populates="groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    programme_assignments = relationship(
        "GroupProgramme",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_groups_school_id", "school_id"),
        Index("ix_groups_teacher_id", "teacher_id"),
    )


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    child_id = Column(String(36), ForeignKey("child_profiles.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    group = relationship("Group", back_populates="members")
    child = relationship("ChildProfile", back_populates="group_memberships")

    __table_args__ = (
        Index("ix_group_members_child_id", "child_id"),
    )


class GroupProgramme(Base):
    __tablename__ = "group_programmes"

    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    programme_id = Column(
        String(36), ForeignKey("programmes.id", ondelete="CASCADE"), primary_key=True
    )
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    group = relationship("Group", back_populates="programme_assignments")
    programme = relationship("Programme", back_populates="group_assignments")

    __table_args__ = (
        Index("ix_group_programmes_programme_id", "programme_id"),
    )