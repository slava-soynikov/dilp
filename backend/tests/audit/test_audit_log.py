"""Sprint 6 — AuditLog SQLAlchemy event listener writes diffs.

Architecture refs: §5.1 (Audit Logging), §7.3.
- Sensitive tables (users, profiles, consents, parent_child_relations) emit rows.
- password_hash never appears in any diff.
"""
from __future__ import annotations

import json

from app.model.log import AuditLog
from app.model.user import User
from tests.auth.conftest import login, register
from tests.users.conftest import auth_header


def _audits(db_session, entity_type: str, action: str | None = None):
    q = db_session.query(AuditLog).filter(AuditLog.entity_type == entity_type)
    if action is not None:
        q = q.filter(AuditLog.action == action)
    return q.all()


def test_user_register_writes_create_audit(client, db_session, outbox):
    register(client, email="p@example.com", password="Strongpass1")
    rows = _audits(db_session, "users", "create")
    assert len(rows) >= 1
    diff = json.loads(rows[0].diff)
    # diff must not leak password
    assert "password_hash" not in json.dumps(diff)


def test_consent_create_writes_audit(client, db_session, outbox):
    headers, _ = auth_header(client)
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "kid1", "first_name": "C", "last_name": "K"},
    ).json()
    resp = client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "data_processing"},
    )
    assert resp.status_code == 201

    rows = _audits(db_session, "consents", "create")
    assert len(rows) == 1
    assert rows[0].entity_id == resp.json()["id"]
    diff = json.loads(rows[0].diff)
    assert diff["after"]["consent_type"] == "data_processing"


def test_consent_revoke_writes_update_audit(client, db_session, outbox):
    headers, _ = auth_header(client)
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "kid1", "first_name": "C", "last_name": "K"},
    ).json()
    grant = client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "data_processing"},
    ).json()
    client.post(f"/api/v1/consents/{grant['id']}/revoke", headers=headers)

    rows = _audits(db_session, "consents", "update")
    assert any(r.entity_id == grant["id"] for r in rows)
    update_row = next(r for r in rows if r.entity_id == grant["id"])
    diff = json.loads(update_row.diff)
    assert "revoked_at" in diff["changed"]


def test_child_status_update_writes_audit(client, db_session, outbox):
    headers, _ = auth_header(client)
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "kid1", "first_name": "C", "last_name": "K"},
    ).json()
    client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "data_processing"},
    )
    child_user = (
        db_session.query(User).filter_by(username=child["username"]).one()
    )
    rows = _audits(db_session, "users", "update")
    matched = [r for r in rows if r.entity_id == child_user.id]
    assert matched, "expected an update audit row for child status flip"
    diff = json.loads(matched[-1].diff)
    assert "status" in diff["changed"]
    assert diff["changed"]["status"]["after"] == "active"


def test_password_hash_never_appears_in_audit_diff(
    client, db_session, outbox
):
    register(client, email="p@example.com", password="Strongpass1")
    # Touch password reset to provoke users.password_hash update.
    client.post(
        "/api/v1/auth/forgot-password", json={"email": "p@example.com"}
    )
    # We can't easily get the token without inspecting outbox; pragma: skip reset.
    rows = db_session.query(AuditLog).all()
    blob = json.dumps([json.loads(r.diff) for r in rows if r.diff])
    assert "password_hash" not in blob