"""seed roles

Revision ID: 0002_seed_roles
Revises: 0001_initial_schema
Create Date: 2026-05-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_seed_roles"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLES = ("child", "parent", "teacher", "admin")


def upgrade() -> None:
    for r in ROLES:
        op.execute(sa.text("INSERT IGNORE INTO roles (name) VALUES (:n)").bindparams(n=r))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM roles WHERE name IN ('child','parent','teacher','admin')"))