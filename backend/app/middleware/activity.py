"""ActivityLog middleware (Sprint 6).

Architecture refs: §5.1 (Activity Tracking), §7.3 (Audit Logging).

Behaviour
---------
For a small allow-list of endpoints we write an ``ActivityLog`` row after the
response is produced, but only when the response is a success (2xx). Failure
paths (401/403/422) are intentionally **not** logged to avoid polluting the
behavioural trail with rejected requests.

The middleware also sets/resets ``current_user_id`` in the request-scoped
``ContextVar`` so SQLAlchemy event listeners can attribute audit rows to the
actor.

User identification
-------------------
* For most endpoints the user comes from the ``Authorization: Bearer ...``
  header (decoded with the same key as the rest of the app).
* For ``POST /api/v1/auth/login`` the user is not authenticated yet on the
  way in — we read ``sub`` from the access token returned in the response.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_token
from app.middleware.context import current_user_id

logger = logging.getLogger("activity")


@dataclass(frozen=True)
class _Rule:
    method: str
    pattern: re.Pattern[str]
    action: str
    entity_type: str | None
    entity_group: int | None  # which regex group holds entity_id, None = no entity


_RULES: list[_Rule] = [
    _Rule("POST", re.compile(r"^/api/v1/auth/login/?$"), "login", None, None),
    _Rule("POST", re.compile(r"^/api/v1/auth/register/?$"), "register", "user", None),
    _Rule("POST", re.compile(r"^/api/v1/auth/logout/?$"), "logout", None, None),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/auth/reset-password/?$"),
        "password_reset",
        None,
        None,
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/auth/forgot-password/?$"),
        "password_forgot",
        None,
        None,
    ),
    _Rule(
        "GET",
        re.compile(r"^/api/v1/lessons/([^/]+)/?$"),
        "lesson_open",
        "lesson",
        1,
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/progress/modules/([^/]+)/start/?$"),
        "module_start",
        "module",
        1,
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/progress/modules/([^/]+)/complete/?$"),
        "module_complete",
        "module",
        1,
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/progress/lessons/([^/]+)/start/?$"),
        "lesson_start",
        "lesson",
        1,
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/progress/lessons/([^/]+)/complete/?$"),
        "lesson_complete",
        "lesson",
        1,
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/consents/?$"),
        "consent_grant",
        "consent",
        None,  # entity_id read from response body
    ),
    _Rule(
        "POST",
        re.compile(r"^/api/v1/consents/([^/]+)/revoke/?$"),
        "consent_revoke",
        "consent",
        1,
    ),
]


def _match_rule(method: str, path: str) -> tuple[_Rule, re.Match[str]] | None:
    for rule in _RULES:
        if rule.method != method:
            continue
        m = rule.pattern.match(path)
        if m:
            return rule, m
    return None


def _user_id_from_authorization(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None


def _user_id_from_login_response(body: bytes) -> str | None:
    try:
        data = json.loads(body)
    except Exception:
        return None
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str):
        return None
    try:
        payload = decode_token(token)
    except Exception:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None


def _entity_id_from_response_body(body: bytes) -> str | None:
    try:
        data = json.loads(body)
    except Exception:
        return None
    if isinstance(data, dict):
        eid = data.get("id")
        return eid if isinstance(eid, str) else None
    return None


class ActivityLogMiddleware(BaseHTTPMiddleware):
    """Sets request user context and writes ActivityLog for known endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        path = request.url.path

        user_id = _user_id_from_authorization(request)
        token = current_user_id.set(user_id)
        try:
            response = await call_next(request)
        finally:
            current_user_id.reset(token)

        if response.status_code >= 400:
            return response

        matched = _match_rule(method, path)
        if not matched:
            return response

        rule, m = matched

        # Buffer the response body so we can both inspect it (for login and
        # consent_grant) and forward it unchanged to the client.
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        log_user_id = user_id
        entity_id: str | None = None
        if rule.entity_group is not None:
            entity_id = m.group(rule.entity_group)

        if rule.action == "login":
            log_user_id = _user_id_from_login_response(body) or log_user_id
        elif rule.action == "register":
            new_user_id = _entity_id_from_response_body(body)
            log_user_id = new_user_id or log_user_id
            entity_id = new_user_id
        elif rule.action == "consent_grant":
            entity_id = _entity_id_from_response_body(body)

        try:
            self._write(request, log_user_id, rule, entity_id)
        except Exception:  # pragma: no cover — never break the request on logging
            logger.exception("activity_log.write_failed")

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    def _write(
        self,
        request: Request,
        user_id: str | None,
        rule: _Rule,
        entity_id: str | None,
    ) -> None:
        # Lazy imports avoid a settings/import cycle at module load time.
        from app.db.session import SessionLocal, get_db
        from app.model.log import ActivityLog

        overrides = getattr(request.app, "dependency_overrides", {}) or {}
        dep = overrides.get(get_db)
        if dep is not None:
            gen = dep()
            db = next(gen)
            close = lambda: _exhaust(gen)
        else:
            db = SessionLocal()
            close = db.close

        try:
            db.add(
                ActivityLog(
                    user_id=user_id,
                    action=rule.action,
                    entity_type=rule.entity_type,
                    entity_id=entity_id,
                )
            )
            db.commit()
        finally:
            try:
                close()
            except Exception:  # pragma: no cover
                pass


def _exhaust(gen) -> None:
    try:
        next(gen)
    except StopIteration:
        pass