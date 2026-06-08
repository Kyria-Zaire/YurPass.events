"""create events table

Revision ID: 20260608_008
Revises: 20260608_007
Create Date: 2026-06-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260608_008"
down_revision: str | None = "20260608_007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

event_type_enum = postgresql.ENUM(
    "nightclub",
    "festival",
    "concert",
    "conference",
    "association",
    "sports",
    "other",
    name="event_type",
    create_type=False,
)

event_status_enum = postgresql.ENUM(
    "draft",
    "published",
    "sold_out",
    "cancelled",
    "archived",
    name="event_status",
    create_type=False,
)

event_visibility_enum = postgresql.ENUM(
    "public",
    "unlisted",
    "private",
    name="event_visibility",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    event_type_enum.create(bind, checkfirst=True)
    event_status_enum.create(bind, checkfirst=True)
    event_visibility_enum.create(bind, checkfirst=True)

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", event_type_enum, nullable=False),
        sa.Column(
            "status",
            event_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "visibility",
            event_visibility_enum,
            nullable=False,
            server_default="public",
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cover_image_url", sa.String(length=2048), nullable=True),
        sa.Column("venue_name", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_slug"), "events", ["slug"], unique=True)
    op.create_index(
        op.f("ix_events_organization_id"),
        "events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_events_status"), "events", ["status"], unique=False)
    op.create_index(
        op.f("ix_events_visibility"),
        "events",
        ["visibility"],
        unique=False,
    )
    op.create_index(
        op.f("ix_events_starts_at"),
        "events",
        ["starts_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_events_starts_at"), table_name="events")
    op.drop_index(op.f("ix_events_visibility"), table_name="events")
    op.drop_index(op.f("ix_events_status"), table_name="events")
    op.drop_index(op.f("ix_events_organization_id"), table_name="events")
    op.drop_index(op.f("ix_events_slug"), table_name="events")
    op.drop_table("events")
    bind = op.get_bind()
    event_visibility_enum.drop(bind, checkfirst=True)
    event_status_enum.drop(bind, checkfirst=True)
    event_type_enum.drop(bind, checkfirst=True)
