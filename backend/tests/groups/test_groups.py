"""/groups CRUD + RBAC scoping."""
from tests.tenants.conftest import login_as, _seed_teacher
from tests.users.conftest import auth_header


def _bootstrap(client, admin_headers):
    """Create a tenant + school + teacher; return ids/headers needed for tests."""
    tenant = client.post(
        "/api/v1/tenants", headers=admin_headers, json={"name": "T"}
    ).json()
    school = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": tenant["id"], "name": "S"},
    ).json()
    return tenant, school


def test_admin_creates_group(client, db_session, admin_headers):
    _, school = _bootstrap(client, admin_headers)
    _, _, teacher_id = _seed_teacher(db_session)

    resp = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": teacher_id, "name": "G1"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["school_id"] == school["id"]


def test_teacher_cannot_create_group(client, db_session, admin_headers):
    _, school = _bootstrap(client, admin_headers)
    email, password, teacher_id = _seed_teacher(db_session, email="t2@example.com")
    headers = login_as(client, email, password)

    resp = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"school_id": school["id"], "teacher_id": teacher_id, "name": "X"},
    )
    assert resp.status_code == 403


def test_teacher_lists_only_own_groups(client, db_session, admin_headers):
    _, school = _bootstrap(client, admin_headers)
    email_a, pwd_a, t_a = _seed_teacher(db_session, email="ta@example.com")
    email_b, pwd_b, t_b = _seed_teacher(db_session, email="tb@example.com")

    g_a = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": t_a, "name": "A"},
    ).json()
    client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": t_b, "name": "B"},
    )

    h_a = login_as(client, email_a, pwd_a)
    resp = client.get("/api/v1/groups", headers=h_a)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1 and body[0]["id"] == g_a["id"]


def test_parent_sees_only_groups_with_own_child(client, db_session, admin_headers, outbox):
    _, school = _bootstrap(client, admin_headers)
    _, _, teacher_id = _seed_teacher(db_session)
    g = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": teacher_id, "name": "G"},
    ).json()

    # Parent without any child in the group
    headers, _ = auth_header(client, email="p1@example.com")
    resp = client.get("/api/v1/groups", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    # Now add this parent's child to the group via teacher
    kid = client.post(
        "/api/v1/children",
        headers=headers,
        json={"username": "kidg", "first_name": "K", "last_name": "G"},
    ).json()
    # Teacher of the group adds the child
    from tests.tenants.conftest import _seed_teacher as _st
    # Use the existing teacher we created; get login
    # Actually, the teacher created via _seed_teacher earlier has a default email.
    # We need a known credentials. Re-create via known email.

    email_t, pwd_t, t_id = _st(db_session, email="t_for_parent@example.com")
    # Create a new group for that known teacher
    g2 = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": t_id, "name": "G2"},
    ).json()
    h_t = login_as(client, email_t, pwd_t)

    add = client.post(
        f"/api/v1/groups/{g2['id']}/members",
        headers=h_t,
        json={"child_id": kid["id"]},
    )
    assert add.status_code == 201, add.text

    resp2 = client.get("/api/v1/groups", headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["id"] == g2["id"]


def test_admin_deletes_group(client, db_session, admin_headers):
    _, school = _bootstrap(client, admin_headers)
    _, _, teacher_id = _seed_teacher(db_session)
    g = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={"school_id": school["id"], "teacher_id": teacher_id, "name": "D"},
    ).json()

    resp = client.delete(f"/api/v1/groups/{g['id']}", headers=admin_headers)
    assert resp.status_code == 204
