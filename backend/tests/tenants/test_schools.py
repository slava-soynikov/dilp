"""/schools CRUD — admin creates, scoped reads for non-admins."""
from tests.users.conftest import auth_header


def _make_tenant(client, admin_headers, name="T1"):
    return client.post("/api/v1/tenants", headers=admin_headers, json={"name": name}).json()


def test_admin_creates_and_lists_schools(client, admin_headers):
    t = _make_tenant(client, admin_headers)
    s1 = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": t["id"], "name": "Schule 1"},
    )
    assert s1.status_code == 201
    s2 = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": t["id"], "name": "Schule 2"},
    )
    assert s2.status_code == 201

    resp = client.get("/api/v1/schools", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_parent_cannot_create_school(client, admin_headers, outbox):
    t = _make_tenant(client, admin_headers)
    headers, _ = auth_header(client)
    resp = client.post(
        "/api/v1/schools",
        headers=headers,
        json={"tenant_id": t["id"], "name": "X"},
    )
    assert resp.status_code == 403


def test_parent_school_list_is_scoped(client, admin_headers, outbox, db_session):
    """Parent without any school-attached children sees an empty list."""
    t = _make_tenant(client, admin_headers)
    client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": t["id"], "name": "Hidden"},
    )
    headers, _ = auth_header(client)
    resp = client.get("/api/v1/schools", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_admin_deletes_school(client, admin_headers):
    t = _make_tenant(client, admin_headers)
    s = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": t["id"], "name": "Del"},
    ).json()
    resp = client.delete(f"/api/v1/schools/{s['id']}", headers=admin_headers)
    assert resp.status_code == 204
