from app.model.user import User

from .conftest import login


def test_login_success(client, verified_parent):
    resp = login(client, verified_parent["email"], verified_parent["password"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_wrong_password(client, verified_parent):
    resp = login(client, verified_parent["email"], "Wrongpass1")
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = login(client, "noone@example.com", "Whatever1")
    assert resp.status_code == 401


def test_login_email_is_case_insensitive(client, verified_parent):
    resp = login(client, verified_parent["email"].upper(), verified_parent["password"])
    assert resp.status_code == 200


def test_login_increments_failed_count(client, db_session, verified_parent):
    for _ in range(3):
        login(client, verified_parent["email"], "Wrong1Wrong")
    db_session.expire_all()
    user = db_session.query(User).filter_by(email=verified_parent["email"]).one()
    assert user.failed_login_count == 3


def test_login_resets_failed_count_on_success(client, db_session, verified_parent):
    login(client, verified_parent["email"], "Wrong1Wrong")
    login(client, verified_parent["email"], verified_parent["password"])
    db_session.expire_all()
    user = db_session.query(User).filter_by(email=verified_parent["email"]).one()
    assert user.failed_login_count == 0
    assert user.last_login_at is not None