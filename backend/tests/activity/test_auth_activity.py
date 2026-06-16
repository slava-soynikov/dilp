"""Sprint 6 — extra ActivityLog coverage on auth-perimeter events."""
from __future__ import annotations

from app.model.log import ActivityLog
from app.model.user import User
from tests.auth.conftest import login, register


def _rows(db_session, action):
    return (
        db_session.query(ActivityLog)
        .filter(ActivityLog.action == action)
        .all()
    )


def test_register_writes_activity_log(client, db_session, outbox):
    resp = register(client, email="p@example.com", password="Strongpass1")
    assert resp.status_code == 201, resp.text
    user = db_session.query(User).filter_by(email="p@example.com").one()
    rows = _rows(db_session, "register")
    assert len(rows) == 1
    assert rows[0].user_id == user.id
    assert rows[0].entity_type == "user"
    assert rows[0].entity_id == user.id


def test_logout_writes_activity_log(client, db_session, outbox):
    register(client, email="p@example.com", password="Strongpass1")
    tokens = login(client, "p@example.com", "Strongpass1").json()
    resp = client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 204
    rows = _rows(db_session, "logout")
    assert len(rows) == 1


def test_forgot_password_writes_activity_log(client, db_session, outbox):
    register(client, email="p@example.com", password="Strongpass1")
    resp = client.post(
        "/api/v1/auth/forgot-password", json={"email": "p@example.com"}
    )
    assert resp.status_code == 200
    rows = _rows(db_session, "password_forgot")
    assert len(rows) == 1