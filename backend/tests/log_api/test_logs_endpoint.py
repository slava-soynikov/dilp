"""Sprint 6 — read-only /logs/activity and /logs/audit for admin + auditor."""
from __future__ import annotations

from app.core.security import hash_password
from app.model.user import Role, User, UserRole
from tests.auth.conftest import login as _login, register
from tests.conftest import login_as
from tests.users.conftest import auth_header


def _seed_user(db_session, *, email, role_name, password="AuditorPass1234"):
    user = User(
        email=email, password_hash=hash_password(password), status="active"
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name=role_name).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return password


def test_admin_can_list_activity(client, db_session, admin_headers, outbox):
    # produce one activity row (an admin login on the way in)
    resp = client.get("/api/v1/logs/activity", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(r["action"] == "login" for r in data)


def test_admin_can_list_audit(client, db_session, admin_headers, outbox):
    # provoke an audit row via registration
    register(client, email="p@example.com", password="Strongpass1")
    resp = client.get(
        "/api/v1/logs/audit?entity_type=users&action=create",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for row in data:
        assert "password_hash" not in (row.get("diff") or "")


def test_auditor_can_list_logs(client, db_session, outbox):
    pwd = _seed_user(db_session, email="aud@example.com", role_name="auditor")
    headers = login_as(client, "aud@example.com", pwd)
    register(client, email="p@example.com", password="Strongpass1")
    resp = client.get("/api/v1/logs/activity", headers=headers)
    assert resp.status_code == 200
    resp = client.get("/api/v1/logs/audit", headers=headers)
    assert resp.status_code == 200


def test_parent_cannot_read_logs(client, db_session, outbox):
    headers, _ = auth_header(client)
    assert client.get("/api/v1/logs/activity", headers=headers).status_code == 403
    assert client.get("/api/v1/logs/audit", headers=headers).status_code == 403


def test_activity_filter_by_action(client, db_session, admin_headers, outbox):
    register(client, email="p@example.com", password="Strongpass1")
    resp = client.get(
        "/api/v1/logs/activity?action=register", headers=admin_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data and all(r["action"] == "register" for r in data)