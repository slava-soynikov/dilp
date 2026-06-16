"""Lesson CRUD + GET /lessons/{id} content resolution via mocked CMS."""
from tests.programmes.conftest import (
    assign_programme_to_group,
    create_lesson,
    create_module,
    create_programme,
)
from tests.tenants.conftest import _seed_teacher, login_as


def _make_module(client, admin_headers, tenant_and_school):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    return create_module(client, admin_headers, p["id"]), p


def test_admin_creates_lesson(client, admin_headers, tenant_and_school):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    lesson = create_lesson(
        client, admin_headers, m["id"], title="L1", content_ref="lessons/foo"
    )
    assert lesson["title"] == "L1"
    assert lesson["content_ref"] == "lessons/foo"


def test_teacher_creates_lesson_when_programme_assigned(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    m, p = _make_module(client, admin_headers, tenant_and_school)
    assign_programme_to_group(
        client, admin_headers, teacher_in_tenant["group_id"], p["id"]
    )
    resp = client.post(
        f"/api/v1/modules/{m['id']}/lessons",
        headers=teacher_in_tenant["headers"],
        json={"title": "TL", "content_ref": "lessons/x", "order_index": 0},
    )
    assert resp.status_code == 201, resp.text


def test_teacher_cannot_create_lesson_when_unassigned(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    resp = client.post(
        f"/api/v1/modules/{m['id']}/lessons",
        headers=teacher_in_tenant["headers"],
        json={"title": "no", "order_index": 0},
    )
    assert resp.status_code == 403


def test_duplicate_lesson_order_returns_409(
    client, admin_headers, tenant_and_school
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    create_lesson(client, admin_headers, m["id"], title="L1", order_index=0)
    resp = client.post(
        f"/api/v1/modules/{m['id']}/lessons",
        headers=admin_headers,
        json={"title": "L2", "order_index": 0},
    )
    assert resp.status_code == 409


def test_patch_lesson_content_ref(client, admin_headers, tenant_and_school):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"], content_ref="lessons/old")
    resp = client.patch(
        f"/api/v1/lessons/{l['id']}",
        headers=admin_headers,
        json={"content_ref": "lessons/new"},
    )
    assert resp.status_code == 200
    assert resp.json()["content_ref"] == "lessons/new"


def test_delete_lesson(client, admin_headers, tenant_and_school):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"])
    resp = client.delete(f"/api/v1/lessons/{l['id']}", headers=admin_headers)
    assert resp.status_code == 204


def test_get_lesson_resolves_content_via_cms(
    client, admin_headers, tenant_and_school, fake_cms
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"], content_ref="lessons/abc")
    fake_cms.set("lessons/abc", {"data": {"attributes": {"body": "Hello"}}})

    resp = client.get(f"/api/v1/lessons/{l['id']}", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == l["id"]
    assert body["content"] == {"data": {"attributes": {"body": "Hello"}}}
    assert fake_cms.calls == ["lessons/abc"]


def test_get_lesson_without_content_ref_returns_null_content(
    client, admin_headers, tenant_and_school, fake_cms
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"], content_ref=None)

    resp = client.get(f"/api/v1/lessons/{l['id']}", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] is None
    assert fake_cms.calls == []


def test_get_lesson_cms_failure_returns_502(
    client, admin_headers, tenant_and_school, fake_cms
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"], content_ref="lessons/broken")
    fake_cms.fail("lessons/broken")

    resp = client.get(f"/api/v1/lessons/{l['id']}", headers=admin_headers)
    assert resp.status_code == 502


# ---------- meeting_url (conference link) ----------


def test_create_lesson_without_meeting_url_defaults_to_null(
    client, admin_headers, tenant_and_school
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    lesson = create_lesson(client, admin_headers, m["id"])
    assert lesson["meeting_url"] is None


def test_admin_creates_lesson_with_meeting_url(
    client, admin_headers, tenant_and_school
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    url = "https://meet.google.com/abc-defg-hij"
    lesson = create_lesson(client, admin_headers, m["id"], meeting_url=url)
    assert lesson["meeting_url"] == url


def test_teacher_creates_lesson_with_meeting_url_when_assigned(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    m, p = _make_module(client, admin_headers, tenant_and_school)
    assign_programme_to_group(
        client, admin_headers, teacher_in_tenant["group_id"], p["id"]
    )
    url = "https://meet.google.com/xyz-1234-qwe"
    resp = client.post(
        f"/api/v1/modules/{m['id']}/lessons",
        headers=teacher_in_tenant["headers"],
        json={
            "title": "TL",
            "content_ref": None,
            "order_index": 0,
            "meeting_url": url,
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["meeting_url"] == url


def test_patch_lesson_sets_meeting_url(client, admin_headers, tenant_and_school):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"])
    assert l["meeting_url"] is None
    url = "https://zoom.us/j/123456789"
    resp = client.patch(
        f"/api/v1/lessons/{l['id']}",
        headers=admin_headers,
        json={"meeting_url": url},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["meeting_url"] == url


def test_patch_lesson_updates_meeting_url(client, admin_headers, tenant_and_school):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(
        client,
        admin_headers,
        m["id"],
        meeting_url="https://meet.google.com/old-link-aaa",
    )
    new_url = "https://meet.google.com/new-link-bbb"
    resp = client.patch(
        f"/api/v1/lessons/{l['id']}",
        headers=admin_headers,
        json={"meeting_url": new_url},
    )
    assert resp.status_code == 200
    assert resp.json()["meeting_url"] == new_url


def test_patch_lesson_clears_meeting_url(client, admin_headers, tenant_and_school):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(
        client,
        admin_headers,
        m["id"],
        meeting_url="https://meet.google.com/to-clear",
    )
    resp = client.patch(
        f"/api/v1/lessons/{l['id']}",
        headers=admin_headers,
        json={"meeting_url": None},
    )
    assert resp.status_code == 200
    assert resp.json()["meeting_url"] is None


def test_patch_lesson_meeting_url_preserves_other_fields(
    client, admin_headers, tenant_and_school
):
    """Partial PATCH of meeting_url must not wipe title/content_ref."""
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(
        client,
        admin_headers,
        m["id"],
        title="Keep me",
        content_ref="lessons/keep",
    )
    resp = client.patch(
        f"/api/v1/lessons/{l['id']}",
        headers=admin_headers,
        json={"meeting_url": "https://meet.google.com/only"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Keep me"
    assert body["content_ref"] == "lessons/keep"
    assert body["meeting_url"] == "https://meet.google.com/only"


def test_get_lesson_returns_meeting_url(
    client, admin_headers, tenant_and_school, fake_cms
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    url = "https://meet.google.com/visible-to-student"
    l = create_lesson(
        client, admin_headers, m["id"], content_ref=None, meeting_url=url
    )
    resp = client.get(f"/api/v1/lessons/{l['id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["meeting_url"] == url


def test_child_in_group_sees_meeting_url(
    client, admin_headers, tenant_and_school, teacher_in_tenant, child_in_group, fake_cms
):
    m, p = _make_module(client, admin_headers, tenant_and_school)
    assign_programme_to_group(
        client, admin_headers, teacher_in_tenant["group_id"], p["id"]
    )
    url = "https://meet.google.com/student-join"
    l = create_lesson(
        client, admin_headers, m["id"], content_ref=None, meeting_url=url
    )
    resp = client.get(
        f"/api/v1/lessons/{l['id']}", headers=child_in_group["headers"]
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["meeting_url"] == url


def test_teacher_cannot_patch_lesson_meeting_url_when_unassigned(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    m, _ = _make_module(client, admin_headers, tenant_and_school)
    l = create_lesson(client, admin_headers, m["id"])
    resp = client.patch(
        f"/api/v1/lessons/{l['id']}",
        headers=teacher_in_tenant["headers"],
        json={"meeting_url": "https://meet.google.com/nope"},
    )
    assert resp.status_code == 403
