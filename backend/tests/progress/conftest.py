"""Sprint 5 fixtures — set up a child, programme/module/lesson, and group assignment.

Architecture refs:
- §5.1 Progress tracking (module/lesson start, complete)
- §7.3 RBAC: child writes own progress only
"""
from __future__ import annotations

import pytest

from tests.programmes.conftest import (  # noqa: F401  (re-export fixtures)
    fake_cms,
    tenant_and_school,
    teacher_in_tenant,
    other_tenant_and_school,
    child_in_group,
    child_no_group,
    assign_programme_to_group,
    create_lesson,
    create_module,
    create_programme,
    seed_child,
)


@pytest.fixture
def programme_with_lessons(
    client, admin_headers, tenant_and_school, teacher_in_tenant, child_in_group
):
    """Programme assigned to child's group, with 1 module and 2 lessons."""
    tenant, _ = tenant_and_school
    p = create_programme(client, admin_headers, tenant_id=tenant["id"])
    assign_programme_to_group(
        client, admin_headers, child_in_group["group_id"], p["id"]
    )
    m = create_module(client, admin_headers, p["id"], title="M1", order_index=0)
    l1 = create_lesson(
        client, admin_headers, m["id"], title="L1", content_ref=None, order_index=0
    )
    l2 = create_lesson(
        client, admin_headers, m["id"], title="L2", content_ref=None, order_index=1
    )
    return {"programme": p, "module": m, "lessons": [l1, l2]}


@pytest.fixture
def unassigned_programme(client, admin_headers, tenant_and_school):
    """Programme NOT assigned to any group the child is in."""
    tenant, _ = tenant_and_school
    p = create_programme(
        client, admin_headers, name="Other", tenant_id=tenant["id"]
    )
    m = create_module(client, admin_headers, p["id"], title="OM", order_index=0)
    l1 = create_lesson(
        client, admin_headers, m["id"], title="OL", content_ref=None, order_index=0
    )
    return {"programme": p, "module": m, "lesson": l1}
