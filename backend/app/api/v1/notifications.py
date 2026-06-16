from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import ok, raise_service_error, read_list, read_one
from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationRead, UnreadCountRead
from app.services import notification_service
from app.services.errors import ServiceError

router = APIRouter()


@router.get("")
async def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    notifications = await notification_service.list_notifications(
        db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return ok(read_list(NotificationRead, notifications))


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    unread_count = await notification_service.count_unread(
        db,
        user_id=current_user.id,
    )
    return ok(UnreadCountRead(unread_count=unread_count).model_dump(mode="json"))


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        notification = await notification_service.mark_read(
            db,
            notification_id=notification_id,
            user_id=current_user.id,
        )
        return ok(
            read_one(NotificationRead, notification),
            message="Notification marked as read",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    result = await notification_service.mark_all_read(db, user_id=current_user.id)
    return ok(result, message="Notifications marked as read")
