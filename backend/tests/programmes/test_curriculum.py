"""Group↔Programme assignment + GET /children/me/curriculum tree."""
from tests.programmes.conftest import (
    assign_programme_to_group,
    create_lesson,
    create_module,
    create_programme,
)
from tests.tenants.conftest import _seed_teacher, login_as
from tests.users.conftest import auth_header


def test_teacher_assigns_programme_to_own_group(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    resp = client.post(
        f"/api/v1/groups/{teacher_in_tenant['group_id']}/programmes",
        headers=teacher_in_tenant["headers"],
        json={"programme_id": p["id"]},
    )
    assert resp.status_code == 201, resp.text


def test_admin_can_assign_to_any_group(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    resp = client.post(
        f"/api/v1/groups/{teacher_in_tenant['group_id']}/programmes",
        headers=admin_headers,
        json={"programme_id": p["id"]},
    )
    assert resp.status_code == 201


def test_teacher_cannot_assign_to_foreign_group(
    client, db_session, admin_headers, tenant_and_school, teacher_in_tenant
):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    # Another teacher with no group
    email, pwd, _ = _seed_teacher(db_session, email="t_outsider@example.com")
    headers = login_as(client, email, pwd)
    resp = client.post(
        f"/api/v1/groups/{teacher_in_tenant['group_id']}/programmes",
        headers=headers,
        json={"programme_id": p["id"]},
    )
    assert resp.status_code == 404


def test_unassign_programme_from_group(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    assign_programme_to_group(
        client, admin_headers, teacher_in_tenant["group_id"], p["id"]
    )
    resp = client.delete(
        f"/api/v1/groups/{teacher_in_tenant['group_id']}/programmes/{p['id']}",
        headers=teacher_in_tenant["headers"],
    )
    assert resp.status_code == 204


def test_assign_duplicate_is_idempotent(
    client, admin_headers, tenant_and_school, teacher_in_tenant
):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    assign_programme_to_group(
        client, admin_headers, teacher_in_tenant["group_id"], p["id"]
    )
    resp = client.post(
        f"/api/v1/groups/{teacher_in_tenant['group_id']}/programmes",
        headers=admin_headers,
        json={"programme_id": p["id"]},
    )
    assert resp.status_code in (200, 201)


def test_child_curriculum_returns_assigned_programmes(
    client, admin_headers, tenant_and_school, teacher_in_tenant, child_in_group
):
    tenant, _ = tenant_and_school
    p1 = create_programme(client, admin_headers, name="P1", tenant_id=tenant["id"])
    p2 = create_programme(client, admin_headers, name="P2", tenant_id=tenant["id"])
    m1 = create_module(client, admin_headers, p1["id"], title="M1", order_index=0)
    create_lesson(client, admin_headers, m1["id"], title="L1", order_index=0)
    assign_programme_to_group(
        client, admin_headers, child_in_group["group_id"], p1["id"]
    )
    assign_programme_to_group(
        client, admin_headers, child_in_group["group_id"], p2["id"]
    )

    resp = client.get(
        "/api/v1/children/me/curriculum", headers=child_in_group["headers"]
    )
    assert resp.status_code == 200, resp.text
    names = sorted(p["name"] for p in resp.json()["programmes"])
    assert names == ["P1", "P2"]


def test_child_curriculum_empty_when_no_group(client, child_no_group):
    resp = client.get(
        "/api/v1/children/me/curriculum", headers=child_no_group["headers"]
    )
    assert resp.status_code == 200
    assert resp.json() == {"programmes": []}


def test_child_curriculum_tree_shape(
    client, admin_headers, tenant_and_school, child_in_group
):
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, name="P", tenant_id=tenant["id"])
    m = create_module(client, admin_headers, p["id"], title="M1", order_index=0)
    create_lesson(client, admin_headers, m["id"], title="L1", order_index=0)
    create_lesson(client, admin_headers, m["id"], title="L2", order_index=1)
    assign_programme_to_group(
        client, admin_headers, child_in_group["group_id"], p["id"]
    )

    resp = client.get(
        "/api/v1/children/me/curriculum", headers=child_in_group["headers"]
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["programmes"]) == 1
    prog = body["programmes"][0]
    assert prog["modules"][0]["title"] == "M1"
    assert [l["title"] for l in prog["modules"][0]["lessons"]] == ["L1", "L2"]


def test_curriculum_requires_child_role(client):
    headers, _ = auth_header(client, email="parent_curr@example.com")
    resp = client.get("/api/v1/children/me/curriculum", headers=headers)
    assert resp.status_code == 403