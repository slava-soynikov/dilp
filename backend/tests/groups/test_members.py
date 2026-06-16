"""POST/DELETE /groups/{id}/members — only the group's own teacher."""
from tests.tenants.conftest import _seed_teacher, login_as
from tests.users.conftest import auth_header


def _setup(client, admin_headers, db_session):
    tenant = client.post(
        "/api/v1/tenants", headers=admin_headers, json={"name": "T"}
    ).json()
    school = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": tenant["id"], "name": "S"},
    ).json()
    email_t, pwd_t, t_id = _seed_teacher(db_session, email="own@example.com")
    h_t = login_as(client, email_t, pwd_t)
    group = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": t_id, "name": "G"},
    ).json()
    parent_headers, _ = auth_header(client, email="p@example.com")
    kid = client.post(
        "/api/v1/children",
        headers=parent_headers,
        json={"username": "kid.m", "first_name": "K", "last_name": "M"},
    ).json()
    return {"school": school, "group": group, "kid": kid, "h_t": h_t, "h_p": parent_headers}


def test_teacher_adds_own_child_to_group(client, db_session, admin_headers):
    ctx = _setup(client, admin_headers, db_session)
    resp = client.post(
        f"/api/v1/groups/{ctx['group']['id']}/members",
        headers=ctx["h_t"],
        json={"child_id": ctx["kid"]["id"]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["group_id"] == ctx["group"]["id"]
    assert body["child_id"] == ctx["kid"]["id"]


def test_other_teacher_cannot_add_to_group(client, db_session, admin_headers):
    ctx = _setup(client, admin_headers, db_session)
    email_o, pwd_o, _ = _seed_teacher(db_session, email="other@example.com")
    h_o = login_as(client, email_o, pwd_o)
    resp = client.post(
        f"/api/v1/groups/{ctx['group']['id']}/members",
        headers=h_o,
        json={"child_id": ctx["kid"]["id"]},
    )
    assert resp.status_code == 404


def test_parent_cannot_add_to_group(client, db_session, admin_headers):
    ctx = _setup(client, admin_headers, db_session)
    resp = client.post(
        f"/api/v1/groups/{ctx['group']['id']}/members",
        headers=ctx["h_p"],
        json={"child_id": ctx["kid"]["id"]},
    )
    assert resp.status_code == 403


def test_teacher_removes_member(client, db_session, admin_headers):
    ctx = _setup(client, admin_headers, db_session)
    client.post(
        f"/api/v1/groups/{ctx['group']['id']}/members",
        headers=ctx["h_t"],
        json={"child_id": ctx["kid"]["id"]},
    )
    resp = client.delete(
        f"/api/v1/groups/{ctx['group']['id']}/members/{ctx['kid']['id']}",
        headers=ctx["h_t"],
    )
    assert resp.status_code == 204


def test_adding_child_sets_school_id_if_missing(client, db_session, admin_headers):
    """Architecture choice: child without school inherits the group's school on first add."""
    ctx = _setup(client, admin_headers, db_session)
    client.post(
        f"/api/v1/groups/{ctx['group']['id']}/members",
        headers=ctx["h_t"],
        json={"child_id": ctx["kid"]["id"]},
    )
    from app.model.profile import ChildProfile
    db_session.expire_all()
    child = db_session.query(ChildProfile).filter_by(id=ctx["kid"]["id"]).one()
    assert child.school_id == ctx["school"]["id"]


def test_cannot_add_child_from_different_school(client, db_session, admin_headers):
    """Child already attached to school A cannot be added to a group in school B."""
    ctx = _setup(client, admin_headers, db_session)
    # First attach child to school via membership in current group
    client.post(
        f"/api/v1/groups/{ctx['group']['id']}/members",
        headers=ctx["h_t"],
        json={"child_id": ctx["kid"]["id"]},
    )

    # Create another school + group with a different teacher
    other_tenant = client.post(
        "/api/v1/tenants", headers=admin_headers, json={"name": "T2"}
    ).json()
    other_school = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": other_tenant["id"], "name": "S2"},
    ).json()
    email_o, pwd_o, t_o = _seed_teacher(db_session, email="oth@example.com")
    other_group = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": other_school["id"], "teacher_id": t_o, "name": "OG"},
    ).json()
    h_o = login_as(client, email_o, pwd_o)
    resp = client.post(
        f"/api/v1/groups/{other_group['id']}/members",
        headers=h_o,
        json={"child_id": ctx["kid"]["id"]},
    )
    assert resp.status_code == 409
