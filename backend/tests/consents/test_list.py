"""GET /consents — parent lists own consents."""
from tests.users.conftest import auth_header


def test_list_consents_returns_grants(client, outbox):
    headers, _ = auth_header(client)
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "lkk", "first_name": "L", "last_name": "K"},
    ).json()
    client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "data_processing"},
    )

    resp = client.get("/api/v1/consents", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["consent_type"] == "data_processing"
    assert body[0]["revoked_at"] is None


def test_list_consents_isolation(client, outbox):
    h_a, _ = auth_header(client, email="ca@example.com")
    h_b, _ = auth_header(client, email="cb@example.com")
    kid_a = client.post(
        "/api/v1/children",
        headers=h_a,
        json={"username": "kida2", "first_name": "K", "last_name": "A"},
    ).json()
    client.post(
        "/api/v1/consents",
        headers=h_a,
        json={"child_id": kid_a["id"], "consent_type": "data_processing"},
    )
    resp_b = client.get("/api/v1/consents", headers=h_b)
    assert resp_b.status_code == 200
    assert resp_b.json() == []