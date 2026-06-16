"""CRUD /programmes + tenant-scoped visibility."""
from tests.programmes.conftest import create_programme
from tests.tenants.conftest import _seed_teacher, login_as
from tests.users.conftest import auth_header


def test_admin_creates_global_programme(client, admin_headers):
    resp = client.post(
        "/api/v1/programmes",
        headers=admin_headers,
        json={"name": "Global P", "language": "uk", "tenant_id": None},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["tenant_id"] is None
    assert body["name"] == "Global P"


def test_admin_creates_tenant_programme(client, admin_headers, tenant_and_school):
    tenant, _ = tenant_and_school
    body = create_programme(client, admin_headers, tenant_id=tenant["id"])
    assert body["tenant_id"] == tenant["id"]


def test_create_programme_with_unknown_tenant_returns_404(client, admin_headers):
    resp = client.post(
        "/api/v1/programmes",
        headers=admin_headers,
        json={"name": "X", "language": "uk", "tenant_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404


def test_teacher_cannot_create_programme(client, db_session, admin_headers):
    email, password, _ = _seed_teacher(db_session, email="t_create@example.com")
    headers = login_as(client, email, password)
    resp = client.post(
        "/api/v1/programmes",
        headers=headers,
        json={"name": "x", "language": "uk"},
    )
    assert resp.status_code == 403


def test_parent_cannot_create_programme(client):
    headers, _ = auth_header(client, email="p_create@example.com")
    resp = client.post(
        "/api/v1/programmes",
        headers=headers,
        json={"name": "x", "language": "uk"},
    )
    assert resp.status_code == 403


def test_list_programmes_admin_sees_all(
    client, admin_headers, tenant_and_school, other_tenant_and_school
):
    tenant_a, _ = tenant_and_school
    tenant_b, _ = other_tenant_and_school
    create_programme(client, admin_headers, name="A", tenant_id=tenant_a["id"])
    create_programme(client, admin_headers, name="B", tenant_id=tenant_b["id"])
    create_programme(client, admin_headers, name="Global", tenant_id=None)

    resp = client.get("/api/v1/programmes", headers=admin_headers)
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert {"A", "B", "Global"} <= names


def test_teacher_sees_own_tenant_plus_global(
    client, admin_headers, tenant_and_school, teacher_in_tenant, other_tenant_and_school
):
    tenant_a, _ = tenant_and_school
    tenant_b, _ = other_tenant_and_school

    create_programme(client, admin_headers, name="A", tenant_id=tenant_a["id"])
    create_programme(client, admin_headers, name="B", tenant_id=tenant_b["id"])
    create_programme(client, admin_headers, name="Global", tenant_id=None)

    resp = client.get("/api/v1/programmes", headers=teacher_in_tenant["headers"])
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert "A" in names
    assert "Global" in names
    assert "B" not in names


def test_get_programme_returns_tree(client, admin_headers, tenant_and_school):
    from tests.programmes.conftest import create_module, create_lesson

    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    m = create_module(client, admin_headers, p["id"], title="M1", order_index=0)
    create_lesson(client, admin_headers, m["id"], title="L1", order_index=0)
    create_lesson(client, admin_headers, m["id"], title="L2", order_index=1)

    resp = client.get(f"/api/v1/programmes/{p['id']}", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["modules"]) == 1
    assert body["modules"][0]["title"] == "M1"
    titles = [l["title"] for l in body["modules"][0]["lessons"]]
    assert titles == ["L1", "L2"]


def test_admin_patches_programme(client, admin_headers, tenant_and_school):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    resp = client.patch(
        f"/api/v1/programmes/{p['id']}",
        headers=admin_headers,
        json={"name": "renamed"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "renamed"


def test_admin_deletes_programme_cascades(client, admin_headers, tenant_and_school):
    from tests.programmes.conftest import create_module, create_lesson

    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    m = create_module(client, admin_headers, p["id"])
    create_lesson(client, admin_headers, m["id"])

    resp = client.delete(f"/api/v1/programmes/{p['id']}", headers=admin_headers)
    assert resp.status_code == 204

    resp2 = client.get(f"/api/v1/programmes/{p['id']}", headers=admin_headers)
    assert resp2.status_code == 404