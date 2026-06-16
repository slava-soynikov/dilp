"""drop users.email_verified_at — registration no longer requires email verification

Revision ID: 0004_drop_email_verified_at
Revises: 0003_user_username
Create Date: 2026-05-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0004_drop_email_verified_at"
down_revision: Union[str, None] = "0003_user_username"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "email_verified_at")


def downgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))