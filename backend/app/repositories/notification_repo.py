from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.models.notification import Notification
from app.models.staff import StaffProfile
from app.models.user import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def create_notifications(
    db: AsyncSession,
    rows: Sequence[dict[str, Any]],
) -> None:
    if not rows:
        return

    table = Notification.__table__
    stmt = pg_insert(table).values(list(rows))
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["user_id", "dedupe_key"],
        index_where=table.c.dedupe_key.is_not(None),
    )
    await db.execute(stmt)


async def list_active_user_ids_by_roles(
    db: AsyncSession,
    roles: Iterable[UserRole],
) -> list[UUID]:
    role_values = [getattr(role, "value", role) for role in roles]
    if not role_values:
        return []

    stmt = (
        select(User.id)
        .where(
            User.role.in_(role_values),
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
        )
        .order_by(User.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_staff_user_id(db: AsyncSession, staff_id: UUID) -> UUID | None:
    stmt = select(StaffProfile.user_id).where(
        StaffProfile.id == staff_id,
        StaffProfile.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_notifications_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    unread_only: bool = False,
    limit: int = 20,
) -> Sequence[Notification]:
    stmt = (
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.dismissed_at.is_(None),
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))

    result = await db.execute(stmt)
    return result.scalars().all()


async def count_unread_for_user(db: AsyncSession, user_id: UUID) -> int:
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.read_at.is_(None),
        Notification.dismissed_at.is_(None),
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def mark_read(
    db: AsyncSession,
    *,
    notification_id: UUID,
    user_id: UUID,
) -> Notification | None:
    notification = await get_user_notification(
        db,
        notification_id=notification_id,
        user_id=user_id,
    )
    if notification is None:
        return None
    if notification.read_at is None:
        notification.read_at = utc_now()
        await db.flush()
        await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, user_id: UUID) -> int:
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
            Notification.dismissed_at.is_(None),
        )
        .values(read_at=utc_now())
    )
    result = await db.execute(stmt)
    return int(result.rowcount or 0)


async def get_user_notification(
    db: AsyncSession,
    *,
    notification_id: UUID,
    user_id: UUID,
) -> Notification | None:
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
        Notification.dismissed_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
