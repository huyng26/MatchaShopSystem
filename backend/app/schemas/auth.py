from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import UserRole, UserStatus
from app.schemas.common import ORMModel, normalize_email, validate_bcrypt_password


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class AuthUser(ORMModel):
    id: UUID
    email: str
    role: UserRole
    status: UserStatus
    last_login_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: AuthUser
