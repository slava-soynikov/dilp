"""Read-only access to ActivityLog and AuditLog (Sprint 6, §7.3).

Architecture refs:
- §7.3 Auditor (optional, read-only): Zugriff für Prüf- und Kontrollzwecke.
- §7.6 Transparenz und Nachvollziehbarkeit.

Both endpoints are restricted to ``admin`` and ``auditor`` roles. No mutation
endpoints exist by design — logs are append-only from event listeners.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.log import ActivityLog, AuditLog
from app.model.user import User
from app.schema.log import ActivityLogRead, AuditLogRead

router = APIRouter(prefix="/logs", tags=["logs"])

_READERS = ("admin", "auditor")


@router.get("/activity", response_model=list[ActivityLogRead])
def list_activity(
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_role(*_READERS)),
    db: Session = Depends(get_db),
):
    q = db.query(ActivityLog)
    if user_id:
        q = q.filter(ActivityLog.user_id == user_id)
    if action:
        q = q.filter(ActivityLog.action == action)
    if entity_type:
        q = q.filter(ActivityLog.entity_type == entity_type)
    return (
        q.order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/audit", response_model=list[AuditLogRead])
def list_audit(
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_role(*_READERS)),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    return (
        q.order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )