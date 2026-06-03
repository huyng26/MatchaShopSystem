from typing import Annotated, Any
from uuid import UUID

from fastapi import Header, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.core.responses import created_response, success_response
from app.services import ServiceError


def raise_service_error(error: ServiceError) -> None:
    detail: str | dict[str, Any]
    if error.context:
        detail = {"code": error.code, **error.context}
    else:
        detail = error.code
    raise HTTPException(status_code=error.status_code, detail=detail)


def ok(data: Any = None, *, message: str = "Fetched successfully") -> dict[str, Any]:
    return success_response(data=jsonable_encoder(data), message=message)


def created(
    data: Any = None, *, message: str = "Created successfully"
) -> dict[str, Any]:
    return created_response(data=jsonable_encoder(data), message=message)


def read_list(schema: type[BaseModel], rows: Any) -> list[dict[str, Any]]:
    return [jsonable_encoder(schema.model_validate(row)) for row in rows]


def read_one(schema: type[BaseModel], row: Any) -> dict[str, Any]:
    return jsonable_encoder(schema.model_validate(row))


async def require_actor_user_id(
    x_user_id: Annotated[UUID | None, Header(alias="X-User-Id")] = None,
) -> UUID:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="x_user_id_required")
    return x_user_id
