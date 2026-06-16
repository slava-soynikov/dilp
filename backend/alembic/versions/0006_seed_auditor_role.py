"""seed auditor role (Sprint 6 — §7.3 Access Control)

Revision ID: 0006_seed_auditor_role
Revises: 0005_group_programmes
Create Date: 2026-05-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0006_seed_auditor_role"
down_revision: Union[str, None] = "0005_group_programmes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("INSERT IGNORE INTO roles (name) VALUES ('auditor')"))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM roles WHERE name = 'auditor'"))