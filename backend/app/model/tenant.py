import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    schools = relationship("School", back_populates="tenant", cascade="all, delete-orphan")
    programmes = relationship("Programme", back_populates="tenant")


class School(Base):
    __tablename__ = "schools"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="schools")
    groups = relationship("Group", back_populates="school")
    children = relationship("ChildProfile", back_populates="school")

    __table_args__ = (
        Index("ix_schools_tenant_id", "tenant_id"),
    )