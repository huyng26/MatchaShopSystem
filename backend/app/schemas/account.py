from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import UserRole, UserStatus
from app.schemas.common import ORMModel, normalize_email, validate_bcrypt_password


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=72)
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: UserRole | None = None
    status: UserStatus | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value is not None else value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        return validate_bcrypt_password(value) if value is not None else value


class UserResponse(ORMModel):
    id: UUID
    email: str
    role: UserRole
    status: UserStatus
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
