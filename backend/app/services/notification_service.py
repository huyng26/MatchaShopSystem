from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.models.notification import Notification
from app.repositories import notification_repo
from app.services.errors import ServiceError


VALID_SEVERITIES = {"info", "warning", "critical"}


async def notify_user(
    db: AsyncSession,
    user_id: UUID | None,
    *,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "info",
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    action_url: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
    expires_at: datetime | None = None,
) -> None:
    if user_id is None or not _can_use_notifications(db):
        return

    await _create_for_users(
        db,
        [user_id],
        notification_type=notification_type,
        title=title,
        message=message,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
        metadata=metadata,
        dedupe_key=dedupe_key,
        expires_at=expires_at,
    )


async def notify_roles(
    db: AsyncSession,
    roles: Iterable[UserRole],
    *,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "info",
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    action_url: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
    expires_at: datetime | None = None,
) -> None:
    if not _can_use_notifications(db):
        return

    user_ids = await notification_repo.list_active_user_ids_by_roles(db, roles)
    await _create_for_users(
        db,
        user_ids,
        notification_type=notification_type,
        title=title,
        message=message,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
        metadata=metadata,
        dedupe_key=dedupe_key,
        expires_at=expires_at,
    )


async def notify_staff(
    db: AsyncSession,
    staff_id: UUID | None,
    *,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "info",
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    action_url: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
    expires_at: datetime | None = None,
) -> None:
    if staff_id is None or not _can_use_notifications(db):
        return

    user_id = await notification_repo.get_staff_user_id(db, staff_id)
    await notify_user(
        db,
        user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
        metadata=metadata,
        dedupe_key=dedupe_key,
        expires_at=expires_at,
    )


async def list_notifications(
    db: AsyncSession,
    *,
    user_id: UUID,
    unread_only: bool = False,
    limit: int = 20,
) -> Sequence[Notification]:
    return await notification_repo.list_notifications_for_user(
        db,
        user_id=user_id,
        unread_only=unread_only,
        limit=max(1, min(limit, 50)),
    )


async def count_unread(db: AsyncSession, *, user_id: UUID) -> int:
    return await notification_repo.count_unread_for_user(db, user_id)


async def mark_read(
    db: AsyncSession,
    *,
    notification_id: UUID,
    user_id: UUID,
) -> Notification:
    try:
        notification = await notification_repo.mark_read(
            db,
            notification_id=notification_id,
            user_id=user_id,
        )
        if notification is None:
            raise ServiceError("notification_not_found", status_code=404)
        await db.commit()
        return notification
    except Exception:
        await db.rollback()
        raise


async def mark_all_read(db: AsyncSession, *, user_id: UUID) -> dict[str, int]:
    try:
        updated_count = await notification_repo.mark_all_read(db, user_id)
        await db.commit()
        return {"updated_count": updated_count}
    except Exception:
        await db.rollback()
        raise


async def _create_for_users(
    db: AsyncSession,
    user_ids: Iterable[UUID],
    *,
    notification_type: str,
    title: str,
    message: str,
    severity: str,
    entity_type: str | None,
    entity_id: UUID | None,
    action_url: str | None,
    metadata: dict[str, Any] | None,
    dedupe_key: str | None,
    expires_at: datetime | None,
) -> None:
    if severity not in VALID_SEVERITIES:
        raise ServiceError("notification_severity_invalid", status_code=422)

    rows = [
        {
            "user_id": user_id,
            "type": notification_type,
            "severity": severity,
            "title": title,
            "message": message,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action_url": action_url,
            "metadata": metadata or {},
            "dedupe_key": dedupe_key,
            "expires_at": expires_at,
        }
        for user_id in dict.fromkeys(user_ids)
    ]
    await notification_repo.create_notifications(db, rows)


def _can_use_notifications(db: AsyncSession) -> bool:
    return hasattr(db, "execute")
