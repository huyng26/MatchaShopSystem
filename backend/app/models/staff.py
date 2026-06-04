from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    StaffStatus,
    TaskPriority,
    TaskStatus,
    UserRole,
    enum_values,
)
from app.models.base import Base


class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[UserRole] = mapped_column(
        PgEnum(
            UserRole,
            name="user_role",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
    )
    salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    date_joined: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StaffStatus] = mapped_column(
        PgEnum(
            StaffStatus,
            name="staff_status",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
        server_default=StaffStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StaffTask(Base):
    __tablename__ = "staff_tasks"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    staff_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("staff_profiles.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(
        PgEnum(
            TaskPriority,
            name="task_priority",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        PgEnum(
            TaskStatus,
            name="task_status",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
        server_default=TaskStatus.PENDING.value,
    )
    created_by: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
