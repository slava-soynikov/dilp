"""Sprint 7 — fixtures for reporting tests.

Architecture refs:
- §5.1 Reporting (active users, activity overview, group progress, programme funnel)
- §7 GDPR — aggregated, non-personally-identifying data only
- §7.3 RBAC — admin/auditor see global; teacher scoped to own groups; parent only own children
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core.security import hash_password
from app.model.log import ActivityLog
from app.model.profile import (
    ChildProfile,
    ParentChildRelation,
    ParentProfile,
    TeacherProfile,
)
from app.model.user import Role, User, UserRole

from tests.conftest import login_as
from tests.programmes.conftest import (  # noqa: F401  (re-export)
    assign_programme_to_group,
    create_lesson,
    create_module,
    create_programme,
    seed_child,
    tenant_and_school,
    teacher_in_tenant,
    other_tenant_and_school,
    child_in_group,
)


# ---------------- auditor / role helpers ----------------


def _seed_user_with_role(db_session, *, email, password, role_name):
    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name=role_name).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return user


@pytest.fixture
def auditor_headers(client, db_session):
    _seed_user_with_role(
        db_session,
        email="auditor@example.com",
        password="AuditorPass1234",
        role_name="auditor",
    )
    return login_as(client, "auditor@example.com", "AuditorPass1234")


# ---------------- parent linked to a seeded child ----------------


def _seed_parent_linked_to_child(db_session, child_id, *, email="p1@example.com"):
    password = "ParentPass1234"
    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name="parent").one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = ParentProfile(user_id=user.id)
    db_session.add(profile)
    db_session.flush()
    db_session.add(
        ParentChildRelation(parent_id=profile.id, child_id=child_id)
    )
    db_session.commit()
    return {"email": email, "password": password, "parent_profile_id": profile.id}


@pytest.fixture
def parent_linked(client, db_session, child_in_group):
    info = _seed_parent_linked_to_child(db_session, child_in_group["child_id"])
    return {
        **info,
        "headers": login_as(client, info["email"], info["password"]),
        "child_id": child_in_group["child_id"],
    }


@pytest.fixture
def parent_unrelated(client, db_session, child_in_group):
    """A second parent with NO link to the child in the fixture group."""
    info = _seed_parent_linked_to_child  # not used directly; create plain parent
    password = "OtherParentPass1234"
    user = User(
        email="p2@example.com",
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name="parent").one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.add(ParentProfile(user_id=user.id))
    db_session.commit()
    return {
        "email": "p2@example.com",
        "password": password,
        "headers": login_as(client, "p2@example.com", password),
        "other_child_id": child_in_group["child_id"],
    }


# ---------------- programme/module/lesson scaffolding ----------------


@pytest.fixture
def programme_with_modules(
    client, admin_headers, tenant_and_school, teacher_in_tenant, child_in_group
):
    """Programme assigned to child's group, with 2 modules and 2 lessons each."""
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, name="ReportProg", tenant_id=tenant["id"])
    assign_programme_to_group(
        client, admin_headers, child_in_group["group_id"], p["id"]
    )
    modules = []
    for i in range(2):
        m = create_module(
            client, admin_headers, p["id"], title=f"M{i}", order_index=i
        )
        l1 = create_lesson(
            client, admin_headers, m["id"], title=f"M{i}L0",
            content_ref=None, order_index=0,
        )
        l2 = create_lesson(
            client, admin_headers, m["id"], title=f"M{i}L1",
            content_ref=None, order_index=1,
        )
        modules.append({"module": m, "lessons": [l1, l2]})
    return {"programme": p, "modules": modules}


# ---------------- low-level ActivityLog seeding ----------------


def seed_activity(
    db_session,
    user_id: str | None,
    action: str,
    *,
    when: datetime | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    row = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    if when is not None:
        row.created_at = when
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def seed_logs(db_session):
    """Helper for tests to insert ActivityLog rows directly with arbitrary timestamps."""
    return lambda **kw: seed_activity(db_session, **kw)


def utc_days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n)