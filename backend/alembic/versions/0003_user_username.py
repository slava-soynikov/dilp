"""user.username column and nullable email

Revision ID: 0003_user_username
Revises: 0002_seed_roles
Create Date: 2026-05-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0003_user_username"
down_revision: Union[str, None] = "0002_seed_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=False)
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "username")