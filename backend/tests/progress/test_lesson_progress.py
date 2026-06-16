"""Sprint 5 — POST /progress/lessons/{id}/start | /complete | /heartbeat."""
from __future__ import annotations


def test_child_starts_lesson(client, child_in_group, programme_with_lessons):
    lesson = programme_with_lessons["lessons"][0]
    resp = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}/start",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["lesson_id"] == lesson["id"]
    assert data["status"] == "in_progress"
    assert data["started_at"] is not None
    assert data["completed_at"] is None


def test_child_completes_lesson(client, child_in_group, programme_with_lessons):
    lesson = programme_with_lessons["lessons"][0]
    resp = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}/complete",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


def test_lesson_heartbeat_updates_last_accessed(
    client, child_in_group, programme_with_lessons
):
    lesson = programme_with_lessons["lessons"][0]
    started = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}/start",
        headers=child_in_group["headers"],
    ).json()
    beat = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}/heartbeat",
        headers=child_in_group["headers"],
    )
    assert beat.status_code == 200, beat.text
    data = beat.json()
    # last_accessed updated; status preserved as in_progress
    assert data["status"] == "in_progress"
    assert data["last_accessed_at"] >= started["last_accessed_at"]


def test_heartbeat_before_start_creates_in_progress(
    client, child_in_group, programme_with_lessons
):
    lesson = programme_with_lessons["lessons"][1]
    resp = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}/heartbeat",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_completing_all_lessons_autocompletes_module(
    client, child_in_group, programme_with_lessons
):
    module_id = programme_with_lessons["module"]["id"]
    headers = child_in_group["headers"]
    l1, l2 = programme_with_lessons["lessons"]

    # complete the first lesson — module should be in_progress (not yet complete)
    client.post(f"/api/v1/progress/lessons/{l1['id']}/complete", headers=headers)
    # we can verify via module start endpoint behaviour: module exists & in_progress
    # Start module to peek — but completing a lesson should already create row.
    resp_mod = client.post(
        f"/api/v1/progress/modules/{module_id}/start", headers=headers
    )
    assert resp_mod.status_code == 200
    assert resp_mod.json()["status"] == "in_progress"

    # complete the second/last lesson → module auto-completes
    client.post(f"/api/v1/progress/lessons/{l2['id']}/complete", headers=headers)
    # observe module status via /start (idempotent read of state)
    resp_after = client.post(
        f"/api/v1/progress/modules/{module_id}/start", headers=headers
    )
    assert resp_after.status_code == 200
    assert resp_after.json()["status"] == "completed"
    assert resp_after.json()["completed_at"] is not None


def test_child_cannot_progress_lesson_outside_curriculum(
    client, child_in_group, unassigned_programme
):
    resp = client.post(
        f"/api/v1/progress/lessons/{unassigned_programme['lesson']['id']}/start",
        headers=child_in_group["headers"],
    )
    assert resp.status_code == 404


def test_non_child_cannot_write_lesson_progress(
    client, admin_headers, programme_with_lessons
):
    lesson = programme_with_lessons["lessons"][0]
    resp = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}/start",
        headers=admin_headers,
    )
    assert resp.status_code == 403
