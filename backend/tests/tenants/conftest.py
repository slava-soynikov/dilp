"""Shared helpers for Sprint 3 tests: admin/teacher/parent auth bootstrap."""
import pytest

from app.core.security import hash_password
from app.model.profile import TeacherProfile
from app.model.user import Role, User, UserRole


def _seed_admin(db_session, email="admin@example.com", password="AdminPass1234"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name="admin").one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return email, password


def _seed_teacher(db_session, email="teach@example.com", password="TeachPass1234"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name="teacher").one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = TeacherProfile(user_id=user.id, first_name="Test", last_name="Teacher")
    db_session.add(profile)
    db_session.commit()
    return email, password, profile.id


def login_as(client, identifier: str, password: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": identifier, "password": password},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client, db_session):
    email, password = _seed_admin(db_session)
    return login_as(client, email, password)


@pytest.fixture
def teacher(client, db_session):
    email, password, profile_id = _seed_teacher(db_session)
    return {
        "headers": login_as(client, email, password),
        "profile_id": profile_id,
        "email": email,
    }
