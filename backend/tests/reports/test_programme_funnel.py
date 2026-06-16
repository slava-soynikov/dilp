"""GET /reports/programmes/{id}/funnel — per-module funnel.

§5.1 Reporting + §7.3 RBAC:
- admin/auditor see all
- teacher only if one of their groups has the programme assigned
- parent/child forbidden
"""
from __future__ import annotations

from datetime import datetime

from app.model.progress import ModuleProgress


def test_forbidden_for_parent(client, parent_linked, programme_with_modules):
    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel", headers=parent_linked["headers"]
    )
    assert resp.status_code == 403


def test_forbidden_for_child(client, child_in_group, programme_with_modules):
    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 403


def test_admin_can_read(client, admin_headers, programme_with_modules):
    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel", headers=admin_headers
    )
    assert resp.status_code == 200


def test_auditor_can_read(client, auditor_headers, programme_with_modules):
    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel", headers=auditor_headers
    )
    assert resp.status_code == 200


def test_owning_teacher_can_read(
    client, teacher_in_tenant, programme_with_modules
):
    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel",
        headers=teacher_in_tenant["headers"],
    )
    assert resp.status_code == 200


def test_unrelated_teacher_blocked(
    client, db_session, programme_with_modules, other_tenant_and_school
):
    from tests.tenants.conftest import _seed_teacher
    email, password, _ = _seed_teacher(db_session, email="unrelated_t@example.com")
    headers = {"Authorization": "Bearer " + client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    ).json()["access_token"]}
    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel", headers=headers
    )
    assert resp.status_code in (403, 404)


def test_programme_not_found(client, admin_headers):
    resp = client.get(
        "/api/v1/reports/programmes/00000000-0000-0000-0000-000000000000/funnel",
        headers=admin_headers,
    )
    assert resp.status_code == 404


def test_module_counts(
    client, admin_headers, db_session, child_in_group, programme_with_modules
):
    modules = programme_with_modules["modules"]
    m0_id = modules[0]["module"]["id"]
    m1_id = modules[1]["module"]["id"]
    # child starts M0 and completes it; M1 untouched
    db_session.add(
        ModuleProgress(
            child_id=child_in_group["child_id"],
            module_id=m0_id,
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
    )
    db_session.commit()

    pid = programme_with_modules["programme"]["id"]
    resp = client.get(
        f"/api/v1/reports/programmes/{pid}/funnel", headers=admin_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["programme_id"] == pid
    assert body["total_children"] == 1
    by_id = {m["module_id"]: m for m in body["modules"]}
    assert by_id[m0_id]["started"] == 1
    assert by_id[m0_id]["completed"] == 1
    assert by_id[m1_id]["started"] == 0
    assert by_id[m1_id]["completed"] == 0
    # modules are returned in order_index ascending
    assert [m["module_id"] for m in body["modules"]] == [m0_id, m1_id]