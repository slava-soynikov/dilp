"""Sprint 5 — POST /progress/modules/{id}/start | /complete."""
from __future__ import annotations


def test_child_starts_module(client, child_in_group, programme_with_lessons):
    module_id = programme_with_lessons["module"]["id"]
    resp = client.post(
        f"/api/v1/progress/modules/{module_id}/start",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["module_id"] == module_id
    assert data["status"] == "in_progress"
    assert data["started_at"] is not None
    assert data["completed_at"] is None
    assert data["child_id"] == child_in_group["child_id"]


def test_child_start_module_is_idempotent(
    client, child_in_group, programme_with_lessons
):
    module_id = programme_with_lessons["module"]["id"]
    first = client.post(
        f"/api/v1/progress/modules/{module_id}/start",
        headers=child_in_group["headers"],
    ).json()
    second = client.post(
        f"/api/v1/progress/modules/{module_id}/start",
        headers=child_in_group["headers"],
    ).json()
    # idempotent: same row, started_at preserved
    assert first["id"] == second["id"]
    assert first["started_at"] == second["started_at"]
    assert second["status"] == "in_progress"


def test_child_completes_module(client, child_in_group, programme_with_lessons):
    module_id = programme_with_lessons["module"]["id"]
    resp = client.post(
        f"/api/v1/progress/modules/{module_id}/complete",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


def test_child_cannot_start_module_outside_curriculum(
    client, child_in_group, unassigned_programme
):
    resp = client.post(
        f"/api/v1/progress/modules/{unassigned_programme['module']['id']}/start",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 404


def test_child_with_no_group_cannot_start_module(
    client, child_no_group, programme_with_lessons
):
    resp = client.post(
        f"/api/v1/progress/modules/{programme_with_lessons['module']['id']}/start",
        headers=child_no_group["headers"],
    )
    assert resp.status_code == 404


def test_parent_cannot_write_module_progress(
    client, admin_headers, programme_with_lessons
):
    # admin (not child) — endpoint must reject non-children outright
    resp = client.post(
        f"/api/v1/progress/modules/{programme_with_lessons['module']['id']}/start",
        headers=admin_headers,
    )
    assert resp.status_code == 403


def test_unknown_module_returns_404(client, child_in_group):
    resp = client.post(
        "/api/v1/progress/modules/00000000-0000-0000-0000-000000000000/start",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 404
