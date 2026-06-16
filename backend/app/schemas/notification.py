from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: UUID
    type: str
    severity: str
    title: str
    message: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    action_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    read_at: datetime | None = None
    created_at: datetime


class UnreadCountRead(ORMModel):
    unread_count: int
