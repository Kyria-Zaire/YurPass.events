"""auth foundation — users and organization_members placeholder

Revision ID: 20260608_001
Revises:
Create Date: 2026-06-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260608_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_status_enum = postgresql.ENUM(
    "active",
    "pending_verification",
    "suspended",
    "deleted",
    name="user_status",
    create_type=False,
)

global_role_enum = postgresql.ENUM(
    "user",
    "admin",
    "super_admin",
    name="global_role",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_status_enum.create(bind, checkfirst=True)
    global_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "status",
            user_status_enum,
            nullable=False,
            server_default="pending_verification",
        ),
        sa.Column(
            "global_role",
            global_role_enum,
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("organization_members", if_exists=True)
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    bind = op.get_bind()
    global_role_enum.drop(bind, checkfirst=True)
    user_status_enum.drop(bind, checkfirst=True)
