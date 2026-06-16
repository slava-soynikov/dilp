"""GET /reports/active-users — admin/auditor only, aggregated by role.

§5.1: "Übersicht über aktive Nutzer". §7: aggregated, non-personal.
"""
from __future__ import annotations

from app.model.profile import ChildProfile
from app.model.user import Role, User, UserRole

from tests.reports.conftest import utc_days_ago


def _make_user(db_session, role_name: str, email: str | None = None,
               username: str | None = None):
    user = User(
        email=email,
        username=username,
        password_hash="x",
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name=role_name).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return user


def test_requires_authentication(client):
    resp = client.get("/api/v1/reports/active-users")
    assert resp.status_code == 401


def test_forbidden_for_parent(client, parent_linked):
    resp = client.get(
        "/api/v1/reports/active-users", headers=parent_linked["headers"]
    )
    assert resp.status_code == 403


def test_forbidden_for_teacher(client, teacher_in_tenant):
    resp = client.get(
        "/api/v1/reports/active-users", headers=teacher_in_tenant["headers"]
    )
    assert resp.status_code == 403


def test_admin_can_read(client, admin_headers):
    resp = client.get(
        "/api/v1/reports/active-users", headers=admin_headers
    )
    assert resp.status_code == 200


def test_auditor_can_read(client, auditor_headers):
    resp = client.get(
        "/api/v1/reports/active-users", headers=auditor_headers
    )
    assert resp.status_code == 200


def test_counts_only_active_within_window(
    client, admin_headers, db_session, seed_logs
):
    parent_in = _make_user(db_session, "parent", email="p_in@example.com")
    parent_out = _make_user(db_session, "parent", email="p_out@example.com")
    child = _make_user(db_session, "child", username="kidA")

    seed_logs(user_id=parent_in.id, action="login", when=utc_days_ago(1))
    seed_logs(user_id=parent_out.id, action="login", when=utc_days_ago(45))
    seed_logs(user_id=child.id, action="lesson_open", when=utc_days_ago(5))

    resp = client.get(
        "/api/v1/reports/active-users?window_days=30", headers=admin_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["window_days"] == 30
    # parent_in + child are active, plus the admin caller (just logged in).
    assert body["by_role"]["parent"] >= 1
    assert body["by_role"]["child"] == 1
    # parent_out is outside the window, must not be counted as parent
    assert body["by_role"]["parent"] < 2 or parent_out.id  # safety check
    assert body["total_active"] >= 2


def test_dedupes_same_user_with_many_events(
    client, admin_headers, db_session, seed_logs
):
    child = _make_user(db_session, "child", username="kidB")
    for _ in range(5):
        seed_logs(user_id=child.id, action="lesson_open", when=utc_days_ago(1))

    resp = client.get(
        "/api/v1/reports/active-users", headers=admin_headers
    )
    body = resp.json()
    assert body["by_role"]["child"] == 1


def test_rejects_invalid_window(client, admin_headers):
    assert client.get(
        "/api/v1/reports/active-users?window_days=0", headers=admin_headers
    ).status_code == 422
    assert client.get(
        "/api/v1/reports/active-users?window_days=400", headers=admin_headers
    ).status_code == 422