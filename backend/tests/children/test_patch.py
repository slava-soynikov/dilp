"""PATCH /children/{id} + cross-parent isolation."""
from tests.users.conftest import auth_header


def _create(client, headers, username="patchkid"):
    return client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": username, "first_name": "A", "last_name": "B"},
    ).json()


def test_patch_own_child(client, outbox):
    headers, _ = auth_header(client)
    kid = _create(client, headers)
    resp = client.patch(
        f"/api/v1/children/{kid['id']}",
        headers=headers,
        json={"first_name": "Anna", "native_language": "uk"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["first_name"] == "Anna"
    assert resp.json()["native_language"] == "uk"


def test_patch_other_parents_child_404(client, outbox):
    h_a, _ = auth_header(client, email="px@example.com")
    h_b, _ = auth_header(client, email="py@example.com")
    kid = _create(client, h_a, username="other.kid")

    resp = client.patch(
        f"/api/v1/children/{kid['id']}",
        headers=h_b,
        json={"first_name": "Bad"},
    )
    assert resp.status_code == 404


def test_patch_unknown_child_404(client, outbox):
    headers, _ = auth_header(client)
    resp = client.patch(
        "/api/v1/children/00000000-0000-0000-0000-000000000000",
        headers=headers,
        json={"first_name": "X"},
    )
    assert resp.status_code == 404


def test_parents_me_get(client, outbox):
    headers, _ = auth_header(client)
    resp = client.get("/api/v1/parents/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["user_id"]
