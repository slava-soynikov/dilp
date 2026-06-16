"""Admin-only POST /admin/teachers + RBAC."""
from app.integrations import mailer
from app.model.profile import TeacherProfile
from app.model.user import Role, User, UserRole
from tests.users.conftest import auth_header


def _login_admin(client, db_session, outbox):
    """Bootstrap an admin user directly in DB and log them in."""
    from app.core.security import hash_password
    user = User(
        email="admin@example.com",
        password_hash=hash_password("Adminpass1"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    admin_role = db_session.query(Role).filter_by(name="admin").one()
    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id))
    db_session.commit()

    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "Adminpass1"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_creates_teacher(client, db_session, outbox):
    headers = _login_admin(client, db_session, outbox)
    mailer.outbox.clear()

    resp = client.post(
        "/api/v1/admin/teachers",
        headers=headers,
        json={"email": "teacher1@example.com", "first_name": "Anna", "last_name": "Schmidt"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "teacher1@example.com"

    # Profile exists, role assigned
    user = db_session.query(User).filter_by(email="teacher1@example.com").one()
    assert db_session.query(TeacherProfile).filter_by(user_id=user.id).one()
    role_names = [r.role.name for r in user.roles]
    assert "teacher" in role_names

    # Temp password mailed
    assert len(mailer.outbox) == 1
    assert mailer.outbox[0]["purpose"] == "teacher_invite"


def test_parent_cannot_create_teacher(client, outbox):
    headers, _ = auth_header(client)
    resp = client.post(
        "/api/v1/admin/teachers",
        headers=headers,
        json={"email": "teacher2@example.com", "first_name": "Anna", "last_name": "Schmidt"},
    )
    assert resp.status_code == 403


def test_anon_cannot_create_teacher(client):
    resp = client.post(
        "/api/v1/admin/teachers",
        json={"email": "teacher3@example.com", "first_name": "Anna", "last_name": "Schmidt"},
    )
    assert resp.status_code == 401


def test_cli_create_admin(db_session):
    from app.cli import create_admin
    create_admin(db_session, email="boss@example.com", password="BossPass1234")
    user = db_session.query(User).filter_by(email="boss@example.com").one()
    assert user.status == "active"
    role_names = [r.role.name for r in user.roles]
    assert "admin" in role_names