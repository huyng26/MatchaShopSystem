from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    field: str
    message: str


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool
    message: str
    data: DataT | None = None


class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)


class PaginationData(BaseModel, Generic[DataT]):
    items: list[DataT]
    page: int
    page_size: int
    total: int
    total_pages: int


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


def normalize_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value:
        raise ValueError("Email must be valid")
    return value


def validate_non_empty(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Value must not be empty")
    return value


def validate_bcrypt_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 bytes or fewer")
    return value


def to_jsonable(model: BaseModel | list[BaseModel] | Any) -> Any:
    if isinstance(model, list):
        return [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in model
        ]
    if isinstance(model, BaseModel):
        return model.model_dump(mode="json")
    return model
