"""add first_name/last_name to teacher_profiles

Revision ID: 0009_teacher_name
Revises: 0008_user_lockout_until
Create Date: 2026-05-25

UI braucht eine Auswahl-Liste der Lehrkraefte mit Suche nach Nachname statt
manueller UUID-Eingabe.

Backfill: existierende Zeilen bekommen einen Platzhalter aus user.email,
damit die NOT NULL constraint erfuellt ist.

Idempotent: MySQL ist nicht-transaktional fuer DDL, also pruefen wir vor
jedem Schritt den aktuellen Schema-Zustand (frueherer Fehlversuch konnte
Spalten teilweise hinzufuegen).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0009_teacher_name"
down_revision: Union[str, None] = "0008_user_lockout_until"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(bind, table: str) -> set[str]:
    insp = sa.inspect(bind)
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    cols = _columns(bind, "teacher_profiles")

    if "first_name" not in cols:
        op.add_column(
            "teacher_profiles",
            sa.Column("first_name", sa.String(length=100), nullable=True),
        )
    if "last_name" not in cols:
        op.add_column(
            "teacher_profiles",
            sa.Column("last_name", sa.String(length=100), nullable=True),
        )

    op.execute(
        """
        UPDATE teacher_profiles AS tp
        LEFT JOIN users u ON u.id = tp.user_id
        SET tp.first_name = COALESCE(tp.first_name, ''),
            tp.last_name  = COALESCE(tp.last_name, u.email, '')
        """
    )

    op.alter_column(
        "teacher_profiles",
        "first_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        "teacher_profiles",
        "last_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("teacher_profiles", "last_name")
    op.drop_column("teacher_profiles", "first_name")