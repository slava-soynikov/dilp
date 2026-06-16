"""/tenants CRUD — admin only."""
from app.model.tenant import Tenant
from tests.users.conftest import auth_header


def test_admin_creates_tenant(client, db_session, admin_headers):
    resp = client.post(
        "/api/v1/tenants",
        headers=admin_headers,
        json={"name": "ARAG"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "ARAG"
    assert db_session.query(Tenant).filter_by(id=body["id"]).one()


def test_admin_lists_tenants(client, admin_headers):
    client.post("/api/v1/tenants", headers=admin_headers, json={"name": "A"})
    client.post("/api/v1/tenants", headers=admin_headers, json={"name": "B"})
    resp = client.get("/api/v1/tenants", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_parent_cannot_create_tenant(client, outbox):
    headers, _ = auth_header(client)
    resp = client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "Hacked"},
    )
    assert resp.status_code == 403


def test_admin_deletes_tenant(client, db_session, admin_headers):
    t = client.post("/api/v1/tenants", headers=admin_headers, json={"name": "X"}).json()
    resp = client.delete(f"/api/v1/tenants/{t['id']}", headers=admin_headers)
    assert resp.status_code == 204
    assert db_session.query(Tenant).filter_by(id=t["id"]).first() is None


def test_admin_patches_tenant(client, admin_headers):
    t = client.post("/api/v1/tenants", headers=admin_headers, json={"name": "Old"}).json()
    resp = client.patch(
        f"/api/v1/tenants/{t['id']}", headers=admin_headers, json={"name": "New"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
