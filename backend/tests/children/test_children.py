"""Tests for /children — parent creates pending child with username + PIN."""
from app.model.profile import ChildProfile, ParentChildRelation, ParentProfile
from app.model.user import User
from tests.users.conftest import auth_header


def test_create_child_returns_pin_and_username(client, db_session, outbox):
    headers, _email = auth_header(client)
    resp = client.post(
        "/api/v1/children",
        headers=headers,
        json={
            "username": "anna.k",
            "first_name": "Anna",
            "last_name": "Kovalenko",
            "native_language": "uk",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["username"] == "anna.k"
    assert body["first_name"] == "Anna"
    assert body["status"] == "pending"
    pin = body["pin"]
    assert isinstance(pin, str) and len(pin) == 8 and pin.isdigit()

    # User row exists with that username and is in pending
    user = db_session.query(User).filter_by(username="anna.k").one()
    assert user.status == "pending"
    # Linked via ParentChildRelation
    rel = (
        db_session.query(ParentChildRelation)
        .join(ChildProfile, ChildProfile.id == ParentChildRelation.child_id)
        .filter(ChildProfile.user_id == user.id)
        .one()
    )
    assert rel is not None


def test_create_child_invalid_username_format(client, outbox):
    headers, _ = auth_header(client)
    for bad in ["AB", "with space", "Upper", "weird!", "a" * 65]:
        resp = client.post(
            "/api/v1/children",
            headers=headers,
            json={"username": bad, "first_name": "A", "last_name": "B"},
        )
        assert resp.status_code == 422, f"username={bad}"


def test_create_child_username_must_be_unique(client, outbox):
    headers, _ = auth_header(client)
    body = {"username": "dupkid", "first_name": "A", "last_name": "B"}
    assert client.post("/api/v1/children", headers=headers, json=body).status_code == 201
    assert client.post("/api/v1/children", headers=headers, json=body).status_code == 409


def test_list_children_returns_only_own(client, db_session, outbox):
    headers_a, _ = auth_header(client, email="parent.a@example.com")
    headers_b, _ = auth_header(client, email="parent.b@example.com")

    client.post(
        "/api/v1/children",
        headers=headers_a,
        json={"username": "kid.a", "first_name": "Kid", "last_name": "A"},
    )
    client.post(
        "/api/v1/children",
        headers=headers_b,
        json={"username": "kid.b", "first_name": "Kid", "last_name": "B"},
    )

    resp_a = client.get("/api/v1/children", headers=headers_a)
    assert resp_a.status_code == 200
    list_a = resp_a.json()
    assert len(list_a) == 1
    assert list_a[0]["username"] == "kid.a"


def test_create_child_forbidden_for_non_parent(client, db_session, outbox):
    """A user without parent role gets 403."""
    headers, email = auth_header(client)
    # Strip parent role
    user = db_session.query(User).filter_by(email=email).one()
    for ur in list(user.roles):
        db_session.delete(ur)
    db_session.commit()

    resp = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "kid", "first_name": "A", "last_name": "B"},
    )
    assert resp.status_code == 403


def test_child_login_with_pin(client, outbox):
    """Child should be able to log in with assigned username + PIN, but only after
    activation (consent). For pending child, login returns 403."""
    headers, _ = auth_header(client)
    resp = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "logink", "first_name": "L", "last_name": "K"},
    )
    pin = resp.json()["pin"]

    # Pending child cannot log in yet
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "logink", "password": pin},
    )
    assert login.status_code == 403