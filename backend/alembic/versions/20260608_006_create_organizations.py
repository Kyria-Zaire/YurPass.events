"""create organizations table

Revision ID: 20260608_006
Revises: 20260608_005
Create Date: 2026-06-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260608_006"
down_revision: str | None = "20260608_005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

organization_type_enum = postgresql.ENUM(
    "nightclub",
    "festival",
    "association",
    "bde",
    "venue",
    "business",
    "independent_organizer",
    "other",
    name="organization_type",
    create_type=False,
)

organization_status_enum = postgresql.ENUM(
    "draft",
    "active",
    "suspended",
    "archived",
    name="organization_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    organization_type_enum.create(bind, checkfirst=True)
    organization_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("type", organization_type_enum, nullable=False),
        sa.Column(
            "status",
            organization_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=2048), nullable=True),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)
    op.create_index(op.f("ix_organizations_type"), "organizations", ["type"], unique=False)
    op.create_index(
        op.f("ix_organizations_status"),
        "organizations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organizations_created_by_user_id"),
        "organizations",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_organizations_created_by_user_id"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_status"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_type"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")
    bind = op.get_bind()
    organization_status_enum.drop(bind, checkfirst=True)
    organization_type_enum.drop(bind, checkfirst=True)
