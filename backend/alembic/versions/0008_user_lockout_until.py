"""add users.lockout_until for per-account brute-force protection

Revision ID: 0008_user_lockout_until
Revises: 0007_widen_log_entity_id
Create Date: 2026-05-23

Architecture §7.2 — erhöhte Schutzanforderungen for children's data. The
global IP rate-limit doesn't stop a distributed attack on a single 8-digit
PIN. Add a per-account cool-down triggered after N consecutive failures.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0008_user_lockout_until"
down_revision: Union[str, None] = "0007_widen_log_entity_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("lockout_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "lockout_until")