"""remove staff salary and staff tasks

Revision ID: 20260617_remove_staff_salary_tasks
Revises: 20260616_add_notifications
Create Date: 2026-06-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260617_remove_staff_salary_tasks"
down_revision: str | None = "20260616_add_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("staff_tasks")
    op.drop_constraint(
        "staff_profiles_salary_non_negative",
        "staff_profiles",
        type_="check",
    )
    op.drop_column("staff_profiles", "salary")
    op.execute("DROP TYPE IF EXISTS task_status")
    op.execute("DROP TYPE IF EXISTS task_priority")


def downgrade() -> None:
    op.add_column("staff_profiles", sa.Column("salary", sa.Numeric(12, 2)))
    op.create_check_constraint(
        "staff_profiles_salary_non_negative",
        "staff_profiles",
        "salary IS NULL OR salary >= 0",
    )
    op.execute(
        "CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent')"
    )
    op.execute("CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'done')")
    op.create_table(
        "staff_tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "staff_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("staff_profiles.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                "urgent",
                name="task_priority",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "in_progress",
                "done",
                name="task_status",
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'pending'::task_status"),
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
