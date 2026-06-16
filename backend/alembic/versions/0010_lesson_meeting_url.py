"""add meeting_url to lessons

Revision ID: 0010_lesson_meeting_url
Revises: 0009_teacher_name
Create Date: 2026-05-28

Teachers can attach a conference link (e.g. Google Meet) to a lesson so
students can join the live session from the lesson view.

Idempotent (MySQL DDL is non-transactional): check existing columns first.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0010_lesson_meeting_url"
down_revision: Union[str, None] = "0009_teacher_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(bind, table: str) -> set[str]:
    insp = sa.inspect(bind)
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    cols = _columns(bind, "lessons")
    if "meeting_url" not in cols:
        op.add_column(
            "lessons",
            sa.Column("meeting_url", sa.String(length=2048), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("lessons", "meeting_url")