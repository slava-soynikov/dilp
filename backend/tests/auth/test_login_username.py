"""Login by username (children) — Sprint 2 prerequisite.

Adults log in with email, children with a parent-assigned username.
The `username` form field of OAuth2PasswordRequestForm accepts either.
"""
from app.core.security import hash_password
from app.model.user import Role, User, UserRole


def _seed_child_user(db_session, username: str, password: str):
    user = User(
        username=username,
        email=None,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name="child").one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return user


def test_login_by_username_success(client, db_session):
    _seed_child_user(db_session, "anna.k-2026", "Kidpass1234")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "anna.k-2026", "password": "Kidpass1234"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


def test_login_by_username_wrong_password(client, db_session):
    _seed_child_user(db_session, "anna.k-2026", "Kidpass1234")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "anna.k-2026", "password": "Wrong9999"},
    )
    assert resp.status_code == 401


def test_login_by_username_is_case_insensitive(client, db_session):
    _seed_child_user(db_session, "anna.k-2026", "Kidpass1234")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "ANNA.K-2026", "password": "Kidpass1234"},
    )
    assert resp.status_code == 200


def test_login_username_not_found(client, db_session):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "ghost", "password": "Whatever1"},
    )
    assert resp.status_code == 401


def test_user_can_have_no_email(client, db_session):
    """Regression: User.email must be nullable for child accounts."""
    user = _seed_child_user(db_session, "noemail-child", "Kidpass1234")
    db_session.expire_all()
    fresh = db_session.query(User).filter_by(id=user.id).one()
    assert fresh.email is None
    assert fresh.username == "noemail-child"