"""Tests for /consents — grant + revoke, with child.status trigger."""
from app.model.user import User
from tests.users.conftest import auth_header


def _create_child(client, headers, username="kidc"):
    resp = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": username, "first_name": "C", "last_name": "K"},
    )
    return resp.json()


def test_grant_consent_activates_child(client, db_session, outbox):
    headers, _ = auth_header(client)
    child = _create_child(client, headers)
    assert child["status"] == "pending"

    resp = client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "data_processing"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["consent_type"] == "data_processing"
    assert body["revoked_at"] is None

    db_session.expire_all()
    child_user = db_session.query(User).filter_by(username=child["username"]).one()
    assert child_user.status == "active"


def test_revoke_consent_reverts_child_to_pending(client, db_session, outbox):
    headers, _ = auth_header(client)
    child = _create_child(client, headers)
    grant = client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "data_processing"},
    ).json()

    resp = client.post(
        f"/api/v1/consents/{grant['id']}/revoke",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["revoked_at"] is not None

    db_session.expire_all()
    child_user = db_session.query(User).filter_by(username=child["username"]).one()
    assert child_user.status == "pending"


def test_grant_consent_other_parent_child_forbidden(client, outbox):
    headers_a, _ = auth_header(client, email="pa@example.com")
    headers_b, _ = auth_header(client, email="pb@example.com")
    kid_a = _create_child(client, headers_a, username="kida")

    resp = client.post(
        "/api/v1/consents",
        headers=headers_b,
        json={"child_id": kid_a["id"], "consent_type": "data_processing"},
    )
    assert resp.status_code == 404


def test_grant_unknown_consent_type_rejected(client, outbox):
    headers, _ = auth_header(client)
    child = _create_child(client, headers)
    resp = client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": child["id"], "consent_type": "marketing"},
    )
    assert resp.status_code == 422


def test_child_can_login_after_consent_granted(client, outbox):
    headers, _ = auth_header(client)
    create_resp = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "loginok", "first_name": "L", "last_name": "K"},
    ).json()
    pin = create_resp["pin"]

    # Before consent — 403
    resp_before = client.post(
        "/api/v1/auth/login",
        data={"username": "loginok", "password": pin},
    )
    assert resp_before.status_code == 403

    # Grant consent
    client.post(
        "/api/v1/consents",
        headers=headers,
        json={"child_id": create_resp["id"], "consent_type": "data_processing"},
    )

    # After consent — 200
    resp_after = client.post(
        "/api/v1/auth/login",
        data={"username": "loginok", "password": pin},
    )
    assert resp_after.status_code == 200, resp_after.text
    assert resp_after.json()["access_token"]
