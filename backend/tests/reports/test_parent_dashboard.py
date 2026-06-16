"""GET /parents/me/children/{id}/dashboard — per-child summary for the linked parent.

§5.1 Reporting + §7.3 RBAC:
- only the parent linked via ParentChildRelation may view this child's dashboard
- any other parent gets 404 (do not reveal the child's existence)
- non-parent roles forbidden
"""
from __future__ import annotations

from datetime import datetime

from app.model.progress import LessonProgress, ModuleProgress


def test_requires_auth(client, child_in_group):
    resp = client.get(
        f"/api/v1/parents/me/children/{child_in_group['child_id']}/dashboard"
    )
    assert resp.status_code == 401


def test_forbidden_for_admin(client, admin_headers, child_in_group):
    """Admin is not a parent; this endpoint is parent-scoped."""
    resp = client.get(
        f"/api/v1/parents/me/children/{child_in_group['child_id']}/dashboard",
        headers=admin_headers,
    )
    assert resp.status_code == 403


def test_forbidden_for_teacher(client, teacher_in_tenant, child_in_group):
    resp = client.get(
        f"/api/v1/parents/me/children/{child_in_group['child_id']}/dashboard",
        headers=teacher_in_tenant["headers"],
    )
    assert resp.status_code == 403


def test_unrelated_parent_gets_404(client, parent_unrelated):
    resp = client.get(
        f"/api/v1/parents/me/children/{parent_unrelated['other_child_id']}/dashboard",
        headers=parent_unrelated["headers"],
    )
    assert resp.status_code == 404


def test_linked_parent_can_read_empty(
    client, parent_linked, programme_with_modules
):
    resp = client.get(
        f"/api/v1/parents/me/children/{parent_linked['child_id']}/dashboard",
        headers=parent_linked["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["child_id"] == parent_linked["child_id"]
    progs = {p["programme_id"]: p for p in body["programmes"]}
    pid = programme_with_modules["programme"]["id"]
    assert pid in progs
    # 2 modules, untouched
    modules = progs[pid]["modules"]
    assert len(modules) == 2
    for m in modules:
        assert m["status"] == "not_started"
        assert m["lessons_total"] == 2
        assert m["lessons_completed"] == 0


def test_dashboard_reflects_progress(
    client, db_session, parent_linked, programme_with_modules
):
    m0 = programme_with_modules["modules"][0]
    m0_id = m0["module"]["id"]
    lessons = m0["lessons"]
    child_id = parent_linked["child_id"]
    # one lesson completed, module marked in_progress
    db_session.add(
        ModuleProgress(
            child_id=child_id,
            module_id=m0_id,
            status="in_progress",
            started_at=datetime.utcnow(),
        )
    )
    db_session.add(
        LessonProgress(
            child_id=child_id,
            lesson_id=lessons[0]["id"],
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
    )
    db_session.commit()

    resp = client.get(
        f"/api/v1/parents/me/children/{child_id}/dashboard",
        headers=parent_linked["headers"],
    )
    body = resp.json()
    pid = programme_with_modules["programme"]["id"]
    prog = next(p for p in body["programmes"] if p["programme_id"] == pid)
    m0_summary = next(m for m in prog["modules"] if m["module_id"] == m0_id)
    assert m0_summary["status"] == "in_progress"
    assert m0_summary["lessons_total"] == 2
    assert m0_summary["lessons_completed"] == 1


def test_unknown_child_returns_404(client, parent_linked):
    resp = client.get(
        "/api/v1/parents/me/children/00000000-0000-0000-0000-000000000000/dashboard",
        headers=parent_linked["headers"],
    )
    assert resp.status_code == 404
