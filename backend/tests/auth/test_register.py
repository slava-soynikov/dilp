from app.model.profile import ParentProfile
from app.model.user import User

from .conftest import register


def test_register_parent_success(client, db_session, outbox):
    resp = register(client, email="parent@example.com")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "parent@example.com"
    assert body["status"] == "active"

    user = db_session.query(User).filter_by(email="parent@example.com").one()
    assert user.password_hash != "Strongpass1"
    # No email-verification mail is sent on registration.
    assert outbox == []


def test_register_parent_auto_creates_parent_profile(client, db_session):
    resp = register(client, email="autoprof@example.com")
    assert resp.status_code == 201
    user = db_session.query(User).filter_by(email="autoprof@example.com").one()
    profile = db_session.query(ParentProfile).filter_by(user_id=user.id).one()
    assert profile.id


def test_register_email_is_normalized_to_lowercase(client, db_session):
    resp = register(client, email="Mixed.Case@Example.COM")
    assert resp.status_code == 201
    assert db_session.query(User).filter_by(email="mixed.case@example.com").one()


def test_register_duplicate_email(client):
    assert register(client, email="dup@example.com").status_code == 201
    assert register(client, email="dup@example.com").status_code == 409


def test_register_duplicate_email_case_insensitive(client):
    assert register(client, email="dup2@example.com").status_code == 201
    assert register(client, email="DUP2@example.com").status_code == 409


def test_register_weak_password_too_short(client):
    resp = register(client, email="weak@example.com", password="Short1")
    assert resp.status_code == 422


def test_register_password_missing_digit(client):
    resp = register(client, email="weak2@example.com", password="OnlyLetters")
    assert resp.status_code == 422


def test_register_role_child_forbidden(client):
    resp = register(client, email="kid@example.com", role="child")
    assert resp.status_code == 403


def test_register_role_admin_forbidden(client):
    resp = register(client, email="root@example.com", role="admin")
    assert resp.status_code == 403


def test_register_role_teacher_forbidden_in_mvp(client):
    resp = register(client, email="t@example.com", role="teacher")
    assert resp.status_code == 403