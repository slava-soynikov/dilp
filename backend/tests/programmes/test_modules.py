"""Module CRUD nested under a programme."""
from tests.programmes.conftest import (
    assign_programme_to_group,
    create_module,
    create_programme,
)
from tests.tenants.conftest import _seed_teacher, login_as


def _make_tenant_programme(client, admin_headers, tenant_and_school):
    tenant, _ = tenant_and_school
    return create_programme(client, admin_headers, tenant_id=tenant["id"]), tenant


def test_admin_creates_module_in_global_programme(client, admin_headers):
    p = create_programme(client, admin_headers, tenant_id=None)
    m = create_module(client, admin_headers, p["id"], title="M0", order_index=0)
    assert m["programme_id"] == p["id"]


def test_teacher_creates_module_when_programme_assigned_to_their_group(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    p, _ = _make_tenant_programme(client, admin_headers, tenant_and_school)
    assign_programme_to_group(
        client, admin_headers, teacher_in_tenant["group_id"], p["id"]
    )

    resp = client.post(
        f"/api/v1/programmes/{p['id']}/modules",
        headers=teacher_in_tenant["headers"],
        json={"title": "T-module", "order_index": 0},
    )
    assert resp.status_code == 201, resp.text


def test_teacher_cannot_create_module_in_unassigned_programme(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    p, _ = _make_tenant_programme(client, admin_headers, tenant_and_school)
    # NOT assigned to teacher's group
    resp = client.post(
        f"/api/v1/programmes/{p['id']}/modules",
        headers=teacher_in_tenant["headers"],
        json={"title": "no", "order_index": 0},
    )
    assert resp.status_code == 403


def test_teacher_in_other_tenant_cannot_create_module(
    client, db_session, admin_headers, tenant_and_school
):
    p, _ = _make_tenant_programme(client, admin_headers, tenant_and_school)
    email, pwd, _ = _seed_teacher(db_session, email="t_other@example.com")
    headers = login_as(client, email, pwd)
    resp = client.post(
        f"/api/v1/programmes/{p['id']}/modules",
        headers=headers,
        json={"title": "x", "order_index": 0},
    )
    assert resp.status_code == 403


def test_duplicate_order_index_returns_409(
    client, admin_headers, tenant_and_school
):
    p, _ = _make_tenant_programme(client, admin_headers, tenant_and_school)
    create_module(client, admin_headers, p["id"], title="A", order_index=0)
    resp = client.post(
        f"/api/v1/programmes/{p['id']}/modules",
        headers=admin_headers,
        json={"title": "B", "order_index": 0},
    )
    assert resp.status_code == 409


def test_patch_module_title(client, admin_headers, tenant_and_school):
    p, _ = _make_tenant_programme(client, admin_headers, tenant_and_school)
    m = create_module(client, admin_headers, p["id"], title="orig", order_index=0)
    resp = client.patch(
        f"/api/v1/modules/{m['id']}",
        headers=admin_headers,
        json={"title": "renamed"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "renamed"


def test_delete_module_cascades_lessons(client, admin_headers, tenant_and_school):
    from tests.programmes.conftest import create_lesson

    p, _ = _make_tenant_programme(client, admin_headers, tenant_and_school)
    m = create_module(client, admin_headers, p["id"])
    create_lesson(client, admin_headers, m["id"])

    resp = client.delete(f"/api/v1/modules/{m['id']}", headers=admin_headers)
    assert resp.status_code == 204

    tree = client.get(f"/api/v1/programmes/{p['id']}", headers=admin_headers).json()
    assert tree["modules"] == []


def test_create_module_unknown_programme_404(client, admin_headers):
    resp = client.post(
        "/api/v1/programmes/00000000-0000-0000-0000-000000000000/modules",
        headers=admin_headers,
        json={"title": "x", "order_index": 0},
    )
    assert resp.status_code == 404