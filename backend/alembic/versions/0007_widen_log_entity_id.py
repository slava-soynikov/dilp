"""widen audit_logs/activity_logs entity_id to fit composite primary keys

Revision ID: 0007_widen_log_entity_id
Revises: 0006_seed_auditor_role
Create Date: 2026-05-23

Composite PKs like (parent_uuid, child_uuid) serialize to 73 chars and overflow
the previous String(64) column on MySQL (error 1406). 255 chars comfortably
fits any composite of UUID/int keys we currently audit.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0007_widen_log_entity_id"
down_revision: Union[str, None] = "0006_seed_auditor_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch:
        batch.alter_column(
            "entity_id",
            existing_type=sa.String(64),
            type_=sa.String(255),
            existing_nullable=False,
        )
    with op.batch_alter_table("activity_logs") as batch:
        batch.alter_column(
            "entity_id",
            existing_type=sa.String(64),
            type_=sa.String(255),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch:
        batch.alter_column(
            "entity_id",
            existing_type=sa.String(255),
            type_=sa.String(64),
            existing_nullable=False,
        )
    with op.batch_alter_table("activity_logs") as batch:
        batch.alter_column(
            "entity_id",
            existing_type=sa.String(255),
            type_=sa.String(64),
            existing_nullable=True,
        )
