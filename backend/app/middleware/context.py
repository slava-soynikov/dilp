"""Per-request context for cross-cutting concerns (activity + audit logging).

The current authenticated user_id is exposed via a ContextVar so SQLAlchemy
event listeners (which receive only Session, not Request) can attribute
mutations to the actor performing them. Reset between requests by the
ActivityLogMiddleware.
"""
from __future__ import annotations

from contextvars import ContextVar

current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)