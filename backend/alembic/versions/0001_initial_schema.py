"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- users / roles ----------
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(32), nullable=False, unique=True),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ---------- tenants / schools ----------
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "schools",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_schools_tenant_id", "schools", ["tenant_id"])

    # ---------- profiles ----------
    op.create_table(
        "child_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("school_id", sa.String(36), sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("native_language", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_child_profiles_school_id", "child_profiles", ["school_id"])

    op.create_table(
        "parent_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "teacher_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "parent_child_relations",
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("parent_profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("child_id", sa.String(36), sa.ForeignKey("child_profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_pcr_child_id", "parent_child_relations", ["child_id"])

    # ---------- groups ----------
    op.create_table(
        "groups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("school_id", sa.String(36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", sa.String(36), sa.ForeignKey("teacher_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_groups_school_id", "groups", ["school_id"])
    op.create_index("ix_groups_teacher_id", "groups", ["teacher_id"])

    op.create_table(
        "group_members",
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("child_id", sa.String(36), sa.ForeignKey("child_profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_group_members_child_id", "group_members", ["child_id"])

    # ---------- programmes / modules / lessons ----------
    op.create_table(
        "programmes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_programmes_tenant_id", "programmes", ["tenant_id"])

    op.create_table(
        "modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("programme_id", sa.String(36), sa.ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("programme_id", "order_index", name="uq_modules_programme_order"),
    )
    op.create_index("ix_modules_programme_id", "modules", ["programme_id"])

    op.create_table(
        "lessons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module_id", sa.String(36), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_ref", sa.String(500), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("module_id", "order_index", name="uq_lessons_module_order"),
    )
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])

    # ---------- progress ----------
    op.create_table(
        "module_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("child_id", sa.String(36), sa.ForeignKey("child_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(36), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("child_id", "module_id", name="uq_module_progress_child_module"),
    )
    op.create_index("ix_module_progress_child_id", "module_progress", ["child_id"])

    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("child_id", sa.String(36), sa.ForeignKey("child_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("child_id", "lesson_id", name="uq_lesson_progress_child_lesson"),
    )
    op.create_index("ix_lesson_progress_child_id", "lesson_progress", ["child_id"])

    # ---------- consents ----------
    op.create_table(
        "consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("parent_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("child_id", sa.String(36), sa.ForeignKey("child_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_type", sa.String(100), nullable=False),
        sa.Column("consent_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("consent_text_ref", sa.String(500), nullable=True),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_consents_child_type", "consents", ["child_id", "consent_type"])
    op.create_index("ix_consents_parent_id", "consents", ["parent_id"])

    # ---------- logs ----------
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_activity_logs_user_created", "activity_logs", ["user_id", "created_at"])
    op.create_index("ix_activity_logs_entity", "activity_logs", ["entity_type", "entity_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"])

    # ---------- seed roles ----------
    op.bulk_insert(
        sa.table(
            "roles",
            sa.column("name", sa.String),
        ),
        [{"name": "child"}, {"name": "parent"}, {"name": "teacher"}, {"name": "admin"}],
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("activity_logs")
    op.drop_table("consents")
    op.drop_table("lesson_progress")
    op.drop_table("module_progress")
    op.drop_table("lessons")
    op.drop_table("modules")
    op.drop_table("programmes")
    op.drop_table("group_members")
    op.drop_table("groups")
    op.drop_table("parent_child_relations")
    op.drop_table("teacher_profiles")
    op.drop_table("parent_profiles")
    op.drop_table("child_profiles")
    op.drop_table("schools")
    op.drop_table("tenants")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")