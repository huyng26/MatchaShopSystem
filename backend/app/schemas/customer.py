from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
