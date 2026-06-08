"""activate organization_members — FK, enums, status, indexes

Revision ID: 20260608_007
Revises: 20260608_006
Create Date: 2026-06-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260608_007"
down_revision: str | None = "20260608_006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

organization_role_enum = postgresql.ENUM(
    "owner",
    "admin",
    "staff",
    "viewer",
    name="organization_role",
    create_type=False,
)

member_status_enum = postgresql.ENUM(
    "active",
    "suspended",
    "left",
    name="member_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    organization_role_enum.create(bind, checkfirst=True)
    member_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "organization_members",
        sa.Column(
            "status",
            member_status_enum,
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "organization_members",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.execute(
        "ALTER TABLE organization_members "
        "ALTER COLUMN role TYPE organization_role "
        "USING role::organization_role"
    )

    op.create_foreign_key(
        "fk_organization_members_organization_id",
        "organization_members",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_organization_members_user_org",
        "organization_members",
        ["user_id", "organization_id"],
    )
    op.create_index(
        op.f("ix_organization_members_user_id"),
        "organization_members",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_members_organization_id"),
        "organization_members",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_members_role"),
        "organization_members",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_members_status"),
        "organization_members",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_org_members_org_role",
        "organization_members",
        ["organization_id", "role"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_org_members_org_role", table_name="organization_members")
    op.drop_index(op.f("ix_organization_members_status"), table_name="organization_members")
    op.drop_index(op.f("ix_organization_members_role"), table_name="organization_members")
    op.drop_index(
        op.f("ix_organization_members_organization_id"),
        table_name="organization_members",
    )
    op.drop_index(op.f("ix_organization_members_user_id"), table_name="organization_members")
    op.drop_constraint(
        "uq_organization_members_user_org",
        "organization_members",
        type_="unique",
    )
    op.drop_constraint(
        "fk_organization_members_organization_id",
        "organization_members",
        type_="foreignkey",
    )
    op.alter_column(
        "organization_members",
        "role",
        existing_type=organization_role_enum,
        type_=sa.String(length=50),
        postgresql_using="role::text",
    )
    op.drop_column("organization_members", "updated_at")
    op.drop_column("organization_members", "status")
    bind = op.get_bind()
    member_status_enum.drop(bind, checkfirst=True)
    organization_role_enum.drop(bind, checkfirst=True)
