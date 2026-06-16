import pytest

from .conftest import login


@pytest.fixture
def tokens(client, verified_parent):
    resp = login(client, verified_parent["email"], verified_parent["password"])
    return resp.json()


def test_refresh_success_rotates(client, tokens):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200, resp.text
    new = resp.json()
    assert new["access_token"]
    assert new["refresh_token"]
    assert new["refresh_token"] != tokens["refresh_token"]


def test_refresh_old_token_revoked_after_rotation(client, tokens):
    client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_refresh_invalid_token(client):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-token"})
    assert resp.status_code == 401


def test_logout_revokes_refresh(client, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert resp.status_code == 204
    again = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert again.status_code == 401