from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1, max_length=1000)


class GeocodeResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: Decimal
    longitude: Decimal
    formatted_address: str
    place_id: str | None = None
    provider: str
    status: str
