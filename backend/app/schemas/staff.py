from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import (
    StaffStatus,
    UserRole,
    UserStatus,
)
from app.schemas.common import (
    ORMModel,
    normalize_email,
    validate_bcrypt_password,
    validate_non_empty,
)


class StaffProfileCreate(BaseModel):
    user_id: UUID | None = None
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=3, max_length=50)
    email: str
    role: UserRole
    date_joined: date
    status: StaffStatus = StaffStatus.ACTIVE
    create_account: bool = False
    account_password: str | None = Field(default=None, min_length=8, max_length=72)
    account_status: UserStatus = UserStatus.ACTIVE

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("full_name", "phone")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return validate_non_empty(value)

    @field_validator("account_password")
    @classmethod
    def validate_account_password(cls, value: str | None) -> str | None:
        return validate_bcrypt_password(value) if value is not None else value


class StaffProfileUpdate(BaseModel):
    user_id: UUID | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = None
    role: UserRole | None = None
    date_joined: date | None = None
    status: StaffStatus | None = None
    create_account: bool = False
    account_password: str | None = Field(default=None, min_length=8, max_length=72)
    account_status: UserStatus = UserStatus.ACTIVE

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value is not None else value

    @field_validator("full_name", "phone")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        return validate_non_empty(value) if value is not None else value

    @field_validator("account_password")
    @classmethod
    def validate_account_password(cls, value: str | None) -> str | None:
        return validate_bcrypt_password(value) if value is not None else value


class StaffProfileResponse(ORMModel):
    id: UUID
    user_id: UUID | None = None
    full_name: str
    phone: str
    email: str
    role: UserRole
    date_joined: date
    status: StaffStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
