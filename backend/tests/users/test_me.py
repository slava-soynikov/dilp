"""Tests for /users/me — GET, PATCH, export, DELETE (soft, cascade)."""
from app.model.profile import ChildProfile, ParentChildRelation, ParentProfile
from app.model.user import RefreshToken, User


def test_get_me_returns_user(client, parent_auth):
    resp = client.get("/api/v1/users/me", headers=parent_auth["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == parent_auth["email"]
    assert "parent" in body["roles"]
    assert "password_hash" not in body


def test_get_me_unauthenticated(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_patch_me_noop(client, parent_auth):
    resp = client.patch(
        "/api/v1/users/me",
        headers=parent_auth["headers"],
        json={},
    )
    assert resp.status_code == 200


def test_export_me_returns_json_attachment(client, parent_auth):
    resp = client.get("/api/v1/users/me/export", headers=parent_auth["headers"])
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert "attachment" in resp.headers.get("content-disposition", "")
    body = resp.json()
    assert "user" in body and body["user"]["email"] == parent_auth["email"]
    assert "password_hash" not in body["user"]
    assert "children" in body
    assert "consents" in body


def test_delete_me_soft_deletes_and_revokes_refresh(client, db_session, parent_auth):
    user = db_session.query(User).filter_by(email=parent_auth["email"]).one()
    refresh_count_before = db_session.query(RefreshToken).filter_by(user_id=user.id).count()
    assert refresh_count_before >= 1

    resp = client.delete("/api/v1/users/me", headers=parent_auth["headers"])
    assert resp.status_code == 204

    db_session.expire_all()
    user_after = db_session.query(User).filter_by(id=user.id).one()
    assert user_after.deleted_at is not None

    active_refresh = (
        db_session.query(RefreshToken)
        .filter_by(user_id=user.id, revoked_at=None)
        .count()
    )
    assert active_refresh == 0


def test_delete_me_cascade_soft_deletes_children(client, db_session, parent_auth):
    """Architecture decision: parent self-delete cascades to all linked children."""
    user = db_session.query(User).filter_by(email=parent_auth["email"]).one()
    parent_profile = db_session.query(ParentProfile).filter_by(user_id=user.id).one()

    child_user = User(username="kid1", password_hash="x", status="active")
    db_session.add(child_user)
    db_session.flush()
    child = ChildProfile(user_id=child_user.id, first_name="Anna", last_name="K")
    db_session.add(child)
    db_session.flush()
    db_session.add(ParentChildRelation(parent_id=parent_profile.id, child_id=child.id))
    db_session.commit()
    child_id, child_user_id = child.id, child_user.id

    resp = client.delete("/api/v1/users/me", headers=parent_auth["headers"])
    assert resp.status_code == 204

    db_session.expire_all()
    child_after = db_session.query(ChildProfile).filter_by(id=child_id).one()
    child_user_after = db_session.query(User).filter_by(id=child_user_id).one()
    assert child_after.deleted_at is not None
    assert child_user_after.deleted_at is not None