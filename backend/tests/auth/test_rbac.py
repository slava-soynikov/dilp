"""RBAC dependency tests via probe endpoints mounted on the test app."""
from fastapi import Depends

from app.api.deps import get_current_user, require_role
from app.main import app

from .conftest import login, register


@app.get("/api/v1/_test/me")
def _probe_me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@app.get("/api/v1/_test/parent-only")
def _probe_parent(user=Depends(require_role("parent"))):
    return {"ok": True}


@app.get("/api/v1/_test/admin-only")
def _probe_admin(user=Depends(require_role("admin"))):
    return {"ok": True}


def _access_token(client, email: str = "rbac@example.com") -> str:
    password = "Strongpass1"
    register(client, email=email, password=password)
    resp = login(client, email, password)
    return resp.json()["access_token"]


def test_get_current_user_no_token(client):
    resp = client.get("/api/v1/_test/me")
    assert resp.status_code == 401


def test_get_current_user_invalid_token(client):
    resp = client.get("/api/v1/_test/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_get_current_user_valid(client):
    token = _access_token(client)
    resp = client.get("/api/v1/_test/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "rbac@example.com"


def test_require_role_allows_matching(client):
    token = _access_token(client)
    resp = client.get("/api/v1/_test/parent-only", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_require_role_rejects_other(client):
    token = _access_token(client)
    resp = client.get("/api/v1/_test/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403