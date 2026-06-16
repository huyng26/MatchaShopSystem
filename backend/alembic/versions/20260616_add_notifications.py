"""add notifications

Revision ID: 20260616_add_notifications
Revises: 20260607_delivery_maps_routing_tracking
Create Date: 2026-06-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260616_add_notifications"
down_revision: str | None = "20260607_delivery_maps_routing_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'info'"),
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(length=100)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action_url", sa.Text()),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("dedupe_key", sa.String(length=255)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("dismissed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="notifications_severity_valid",
        ),
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created_at
        ON notifications (user_id, read_at, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_user_created_at
        ON notifications (user_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_user_dedupe_key
        ON notifications (user_id, dedupe_key)
        WHERE dedupe_key IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("uq_notifications_user_dedupe_key", table_name="notifications")
    op.drop_index("idx_notifications_user_created_at", table_name="notifications")
    op.drop_index(
        "idx_notifications_user_read_created_at",
        table_name="notifications",
    )
    op.drop_table("notifications")
