from typing import Any

from fastapi import APIRouter, Depends

from app.api.v1.deps import ok, raise_service_error
from app.core.permissions import get_current_user
from app.models.user import User
from app.schemas.maps import GeocodeRequest, GeocodeResultRead
from app.services import map_service
from app.services.errors import ServiceError

router = APIRouter()


@router.post("/geocode")
async def geocode_address(
    payload: GeocodeRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        result = await map_service.geocode_address(payload.address)
        return ok(GeocodeResultRead.model_validate(result))
    except ServiceError as error:
        raise_service_error(error)
