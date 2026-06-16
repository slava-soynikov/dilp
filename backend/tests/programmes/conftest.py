"""Shared fixtures for Sprint 4 (programmes/modules/lessons/curriculum) tests."""
from __future__ import annotations

from typing import Any

import pytest

from app.core.security import hash_password
from app.integrations.cms import CMSClient, get_cms_client
from app.main import app
from app.model.group import Group, GroupMember
from app.model.profile import ChildProfile, TeacherProfile
from app.model.user import Role, User, UserRole

from tests.tenants.conftest import _seed_teacher, login_as


# ---------- CMS mock ----------


class FakeCMS:
    """In-memory stand-in for the Strapi CMS client.

    Test sets entries via .set(ref, payload); get_content returns the payload
    or raises CMSError if missing. Calls are recorded for assertions.
    """

    def __init__(self):
        self.store: dict[str, dict[str, Any]] = {}
        self.calls: list[str] = []
        self.raise_for: set[str] = set()

    def set(self, ref: str, payload: dict[str, Any]) -> None:
        self.store[ref] = payload

    def fail(self, ref: str) -> None:
        self.raise_for.add(ref)

    def get_content(self, ref: str) -> dict[str, Any]:
        from app.integrations.cms import CMSError

        self.calls.append(ref)
        if ref in self.raise_for:
            raise CMSError(f"forced failure for {ref}")
        if ref not in self.store:
            raise CMSError(f"not found: {ref}")
        return self.store[ref]


@pytest.fixture
def fake_cms():
    fake = FakeCMS()
    app.dependency_overrides[get_cms_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_cms_client, None)


# ---------- domain bootstrap ----------


@pytest.fixture
def tenant_and_school(client, admin_headers):
    tenant = client.post(
        "/api/v1/tenants", headers=admin_headers, json={"name": "T1"}
    ).json()
    school = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": tenant["id"], "name": "S1"},
    ).json()
    return tenant, school


@pytest.fixture
def teacher_in_tenant(client, db_session, admin_headers, tenant_and_school):
    """Teacher that owns a group inside tenant_and_school."""
    _, school = tenant_and_school
    email, password, teacher_id = _seed_teacher(
        db_session, email="t_owner@example.com"
    )
    group = client.post(
        "/api/v1/groups",
        headers=admin_headers,
        json={
            "school_id": school["id"],
            "teacher_id": teacher_id,
            "name": "G-owner",
        },
    ).json()
    return {
        "email": email,
        "password": password,
        "teacher_id": teacher_id,
        "headers": login_as(client, email, password),
        "group_id": group["id"],
    }


@pytest.fixture
def other_tenant_and_school(client, admin_headers):
    tenant = client.post(
        "/api/v1/tenants", headers=admin_headers, json={"name": "T2"}
    ).json()
    school = client.post(
        "/api/v1/schools",
        headers=admin_headers,
        json={"tenant_id": tenant["id"], "name": "S2"},
    ).json()
    return tenant, school


def seed_child(
    db_session,
    *,
    username: str = "kid1",
    password: str = "KidPass1234",
    school_id: str | None = None,
) -> tuple[ChildProfile, str, str]:
    """Create an active child user (login by username + password)."""
    user = User(
        username=username,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name="child").one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = ChildProfile(
        user_id=user.id,
        first_name="K",
        last_name="One",
        school_id=school_id,
    )
    db_session.add(profile)
    db_session.commit()
    return profile, username, password


@pytest.fixture
def child_in_group(client, db_session, teacher_in_tenant, tenant_and_school):
    _, school = tenant_and_school
    profile, username, password = seed_child(db_session, school_id=school["id"])
    db_session.add(
        GroupMember(group_id=teacher_in_tenant["group_id"], child_id=profile.id)
    )
    db_session.commit()
    return {
        "child_id": profile.id,
        "username": username,
        "password": password,
        "headers": login_as(client, username, password),
        "group_id": teacher_in_tenant["group_id"],
    }


@pytest.fixture
def child_no_group(client, db_session, tenant_and_school):
    _, school = tenant_and_school
    profile, username, password = seed_child(
        db_session, username="kid2", school_id=school["id"]
    )
    return {
        "child_id": profile.id,
        "headers": login_as(client, username, password),
    }


# ---------- programme/module/lesson helpers ----------


def create_programme(
    client, admin_headers, *, name="P1", language="uk", tenant_id=None
) -> dict:
    body = {"name": name, "language": language, "tenant_id": tenant_id}
    resp = client.post("/api/v1/programmes", headers=admin_headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_module(
    client, headers, programme_id: str, *, title="M1", order_index=0
) -> dict:
    resp = client.post(
        f"/api/v1/programmes/{programme_id}/modules",
        headers=headers,
        json={"title": title, "order_index": order_index},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_lesson(
    client,
    headers,
    module_id: str,
    *,
    title="L1",
    content_ref: str | None = "lessons/abc",
    order_index=0,
    meeting_url: str | None = None,
) -> dict:
    body: dict[str, Any] = {
        "title": title,
        "content_ref": content_ref,
        "order_index": order_index,
    }
    if meeting_url is not None:
        body["meeting_url"] = meeting_url
    resp = client.post(
        f"/api/v1/modules/{module_id}/lessons",
        headers=headers,
        json=body,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def assign_programme_to_group(client, headers, group_id: str, programme_id: str) -> dict:
    resp = client.post(
        f"/api/v1/groups/{group_id}/programmes",
        headers=headers,
        json={"programme_id": programme_id},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()