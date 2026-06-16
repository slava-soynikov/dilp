"""GET /reports/groups/{id}/progress — group-scoped progress aggregate.

§5.1 Reporting + §7.3 RBAC:
- admin/auditor see any group
- teacher sees only their own groups
- parent/child forbidden
"""
from __future__ import annotations

from datetime import datetime

from app.model.progress import ModuleProgress


def _mark_module_completed(db_session, child_id: str, module_id: str):
    mp = ModuleProgress(
        child_id=child_id,
        module_id=module_id,
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db_session.add(mp)
    db_session.commit()
    return mp


def test_forbidden_for_parent(client, parent_linked, programme_with_modules, child_in_group):
    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=parent_linked["headers"],
    )
    assert resp.status_code == 403


def test_forbidden_for_child(client, child_in_group, programme_with_modules):
    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 403


def test_owning_teacher_can_read(
    client, teacher_in_tenant, child_in_group, programme_with_modules
):
    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=teacher_in_tenant["headers"],
    )
    assert resp.status_code == 200, resp.text


def test_other_teacher_cannot_read(
    client, db_session, child_in_group, programme_with_modules,
    other_tenant_and_school, admin_headers,
):
    """A teacher unrelated to the group must get 403 or 404 (not visible)."""
    from tests.tenants.conftest import _seed_teacher
    email, password, _ = _seed_teacher(db_session, email="other_t@example.com")
    headers = {"Authorization": "Bearer " + client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    ).json()["access_token"]}
    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=headers,
    )
    assert resp.status_code in (403, 404)


def test_admin_can_read(
    client, admin_headers, child_in_group, programme_with_modules
):
    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=admin_headers,
    )
    assert resp.status_code == 200


def test_auditor_can_read(
    client, auditor_headers, child_in_group, programme_with_modules
):
    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=auditor_headers,
    )
    assert resp.status_code == 200


def test_group_not_found(client, admin_headers):
    resp = client.get(
        "/api/v1/reports/groups/00000000-0000-0000-0000-000000000000/progress",
        headers=admin_headers,
    )
    assert resp.status_code == 404


def test_aggregates_modules_completion(
    client, admin_headers, db_session, child_in_group, programme_with_modules
):
    """One child completes 1 of 2 modules → completion_avg_pct == 50.0."""
    first_module_id = programme_with_modules["modules"][0]["module"]["id"]
    _mark_module_completed(db_session, child_in_group["child_id"], first_module_id)

    resp = client.get(
        f"/api/v1/reports/groups/{child_in_group['group_id']}/progress",
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["group_id"] == child_in_group["group_id"]
    assert body["member_count"] == 1
    progs = {p["programme_id"]: p for p in body["programmes"]}
    pid = programme_with_modules["programme"]["id"]
    assert pid in progs
    summary = progs[pid]
    assert summary["modules_total"] == 2
    assert summary["modules_completed_total"] == 1
    assert abs(summary["completion_avg_pct"] - 50.0) < 0.01


def test_empty_group_is_handled(
    client, admin_headers, db_session, tenant_and_school, teacher_in_tenant
):
    """Group with no members reports member_count=0 and empty/zero programmes."""
    _, school = tenant_and_school
    resp = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={
            "school_id": school["id"],
            "teacher_id": teacher_in_tenant["teacher_id"],
            "name": "Empty",
        },
    )
    assert resp.status_code == 201, resp.text
    gid = resp.json()["id"]
    rep = client.get(
        f"/api/v1/reports/groups/{gid}/progress", headers=admin_headers
    )
    assert rep.status_code == 200
    body = rep.json()
    assert body["member_count"] == 0
    assert body["programmes"] == []
