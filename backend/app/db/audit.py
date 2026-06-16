"""AuditLog SQLAlchemy event listener (Sprint 6).

Architecture refs: §5.1 (Audit Logging), §7.3 (RBAC + traceability).

We listen on ``Session.before_flush`` and inspect pending inserts/updates/deletes
for the subset of tables that hold compliance-relevant or personal data. For each
matching mutation we add an ``AuditLog`` row with a JSON diff (``before`` /
``after`` for inserts/deletes, ``changed`` for updates). Sensitive columns are
redacted — in particular ``password_hash`` is never written into a diff.

The actor's user_id is read from the per-request ``current_user_id`` ContextVar
(set by ``ActivityLogMiddleware``). It may be ``None`` for actions performed
outside an authenticated HTTP request (CLI, migrations, etc.).
"""
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.middleware.context import current_user_id

# Tables whose mutations are audited. Keep narrow and explicit to avoid leaking
# noise from log tables / join-only side effects.
SENSITIVE_TABLES: set[str] = {
    "users",
    "user_roles",
    "child_profiles",
    "parent_profiles",
    "teacher_profiles",
    "parent_child_relations",
    "consents",
    "group_members",
}

# Columns that must never be written to an audit diff.
REDACTED_COLUMNS: set[str] = {"password_hash"}


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _safe_attrs(instance: Any) -> dict[str, Any]:
    mapper = inspect(instance).mapper
    out: dict[str, Any] = {}
    for col in mapper.columns:
        key = col.key
        if key in REDACTED_COLUMNS:
            continue
        try:
            out[key] = getattr(instance, key)
        except Exception:
            out[key] = None
    return out


def _changed_attrs(instance: Any) -> dict[str, dict[str, Any]]:
    state = inspect(instance)
    mapper = state.mapper
    out: dict[str, dict[str, Any]] = {}
    for col in mapper.columns:
        key = col.key
        if key in REDACTED_COLUMNS:
            continue
        hist = state.attrs[key].history
        if not hist.has_changes():
            continue
        before = hist.deleted[0] if hist.deleted else None
        after = hist.added[0] if hist.added else getattr(instance, key)
        out[key] = {"before": before, "after": after}
    return out


def _materialize_pk(instance: Any) -> None:
    """Trigger column ``default`` callables for primary keys so an audit row
    written during ``before_flush`` can reference the same id the database
    will eventually receive (insert path)."""
    mapper = inspect(instance).mapper
    for col in mapper.primary_key:
        if getattr(instance, col.key, None) is not None:
            continue
        default = col.default
        if default is None:
            continue
        arg = getattr(default, "arg", None)
        if callable(arg):
            try:
                value = arg()
            except TypeError:
                # SQLAlchemy wraps user-provided no-arg callables to take a
                # context. Pass None — uuid4-style defaults don't read it.
                value = arg(None)
        else:
            value = arg
        if value is not None:
            setattr(instance, col.key, value)


def _entity_id(instance: Any) -> str:
    state = inspect(instance)
    pk = state.identity
    if pk and len(pk) == 1:
        return str(pk[0])
    if pk:
        return ",".join(str(p) for p in pk)
    try:
        mapper = state.mapper
        vals = [getattr(instance, c.key) for c in mapper.primary_key]
        return ",".join(str(v) for v in vals if v is not None) or ""
    except Exception:  # pragma: no cover
        return ""


def _record(session: Session, action: str, instance: Any, diff: dict) -> None:
    from app.model.log import AuditLog

    table = instance.__tablename__
    entry = AuditLog(
        user_id=current_user_id.get(),
        action=action,
        entity_type=table,
        entity_id=_entity_id(instance),
        diff=json.dumps(diff, default=_json_default),
    )
    session.add(entry)


def _audit_before_flush(session: Session, flush_context, instances) -> None:
    # `session.new/dirty/deleted` snapshot of pending state. Avoid auditing
    # our own AuditLog inserts (and the activity log) to prevent recursion.
    for instance in list(session.new):
        table = getattr(instance, "__tablename__", None)
        if table not in SENSITIVE_TABLES:
            continue
        _materialize_pk(instance)
        _record(session, "create", instance, {"after": _safe_attrs(instance)})

    for instance in list(session.dirty):
        table = getattr(instance, "__tablename__", None)
        if table not in SENSITIVE_TABLES:
            continue
        changed = _changed_attrs(instance)
        if not changed:
            continue
        _record(session, "update", instance, {"changed": changed})

    for instance in list(session.deleted):
        table = getattr(instance, "__tablename__", None)
        if table not in SENSITIVE_TABLES:
            continue
        _record(session, "delete", instance, {"before": _safe_attrs(instance)})


def register() -> None:
    """Idempotent listener registration."""
    if not event.contains(Session, "before_flush", _audit_before_flush):
        event.listen(Session, "before_flush", _audit_before_flush)