import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, validate_non_empty

PHONE_ALLOWED_PATTERN = re.compile(r"^[0-9+\-\s().]+$")


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    note: str | None = None
    loyalty_points: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_non_empty(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    note: str | None = None
    loyalty_points: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return validate_non_empty(value) if value is not None else value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("loyalty_points")
    @classmethod
    def validate_loyalty_points(cls, value: int | None) -> int | None:
        if value is None:
            raise ValueError("Loyalty points must not be null")
        return value


class CustomerResponse(ORMModel):
    id: UUID
    name: str
    phone: str | None = None
    address: str | None = None
    note: str | None = None
    loyalty_points: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return value

    value = value.strip()
    if not value:
        return None
    if not PHONE_ALLOWED_PATTERN.fullmatch(value):
        raise ValueError("Phone number format is invalid")

    digit_count = sum(character.isdigit() for character in value)
    if digit_count < 7 or digit_count > 15:
        raise ValueError("Phone number must contain 7 to 15 digits")

    return value
