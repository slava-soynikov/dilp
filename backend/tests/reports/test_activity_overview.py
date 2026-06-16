"""GET /reports/activity-overview — admin/auditor only, aggregated counts.

§5.1: "Grundlegende Aktivitätsübersichten". §7: aggregated, non-personal.
"""
from __future__ import annotations

from app.model.user import Role, User, UserRole

from tests.reports.conftest import utc_days_ago


def _make_user(db_session, role_name="parent", email="u@example.com"):
    user = User(email=email, password_hash="x", status="active")
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name=role_name).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return user


def test_forbidden_for_teacher(client, teacher_in_tenant):
    resp = client.get(
        "/api/v1/reports/activity-overview", headers=teacher_in_tenant["headers"]
    )
    assert resp.status_code == 403


def test_forbidden_for_parent(client, parent_linked):
    resp = client.get(
        "/api/v1/reports/activity-overview", headers=parent_linked["headers"]
    )
    assert resp.status_code == 403


def test_admin_can_read(client, admin_headers):
    resp = client.get(
        "/api/v1/reports/activity-overview", headers=admin_headers
    )
    assert resp.status_code == 200


def test_auditor_can_read(client, auditor_headers):
    resp = client.get(
        "/api/v1/reports/activity-overview", headers=auditor_headers
    )
    assert resp.status_code == 200


def test_aggregates_by_action_and_day(
    client, admin_headers, db_session, seed_logs
):
    u = _make_user(db_session, email="ovr@example.com")
    seed_logs(user_id=u.id, action="login", when=utc_days_ago(1))
    seed_logs(user_id=u.id, action="login", when=utc_days_ago(1))
    seed_logs(user_id=u.id, action="lesson_open", when=utc_days_ago(2))
    seed_logs(user_id=u.id, action="lesson_open", when=utc_days_ago(40))  # out of window

    resp = client.get(
        "/api/v1/reports/activity-overview?window_days=30", headers=admin_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["window_days"] == 30
    actions = {row["action"]: row["count"] for row in body["by_action"]}
    assert actions.get("login", 0) >= 2
    assert actions.get("lesson_open", 0) == 1
    assert body["total_events"] >= 3
    # by_day buckets are date strings YYYY-MM-DD with positive counts
    days = {row["date"]: row["count"] for row in body["by_day"]}
    assert all(c > 0 for c in days.values())
    assert all(len(d) == 10 for d in days)


def test_response_excludes_user_identifiers(
    client, admin_headers, db_session, seed_logs
):
    """§7 Data Minimization: aggregate report MUST NOT expose user_id."""
    u = _make_user(db_session, email="z@example.com")
    seed_logs(user_id=u.id, action="login", when=utc_days_ago(1))

    resp = client.get(
        "/api/v1/reports/activity-overview", headers=admin_headers
    )
    body = resp.json()
    serialised = str(body)
    assert u.id not in serialised
    assert "user_id" not in body
