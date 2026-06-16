"""group_programmes join table — assigns programmes to groups (Sprint 4)

Revision ID: 0005_group_programmes
Revises: 0004_drop_email_verified_at
Create Date: 2026-05-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0005_group_programmes"
down_revision: Union[str, None] = "0004_drop_email_verified_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_programmes",
        sa.Column(
            "group_id",
            sa.String(36),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "programme_id",
            sa.String(36),
            sa.ForeignKey("programmes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_group_programmes_programme_id", "group_programmes", ["programme_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_group_programmes_programme_id", table_name="group_programmes")
    op.drop_table("group_programmes")
