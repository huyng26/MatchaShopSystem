from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.inventory import InventoryMovementType


class IngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., min_length=1, max_length=50)
    current_stock: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=3
    )
    cost_per_unit: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    minimum_threshold: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=3
    )
    image_url: str | None = None


class IngredientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    current_stock: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=3
    )
    cost_per_unit: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    minimum_threshold: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=3
    )
    image_url: str | None = None


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    unit: str
    current_stock: Decimal
    cost_per_unit: Decimal
    minimum_threshold: Decimal
    has_image: bool = False
    image_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_has_image(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                **data,
                "has_image": bool(data.get("image_url")),
            }

        return {
            "id": getattr(data, "id", None),
            "name": getattr(data, "name", None),
            "unit": getattr(data, "unit", None),
            "current_stock": getattr(data, "current_stock", None),
            "cost_per_unit": getattr(data, "cost_per_unit", None),
            "minimum_threshold": getattr(data, "minimum_threshold", None),
            "has_image": bool(getattr(data, "image_url", None)),
            "image_url": getattr(data, "image_url", None),
        }


class InventoryPurchaseCreate(BaseModel):
    ingredient_id: UUID
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3)
    cost_per_unit: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    supplier_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    purchased_at: datetime


class InventoryPurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    quantity: Decimal
    cost_per_unit: Decimal
    total_cost: Decimal
    supplier_name: str | None = None
    notes: str | None = None
    purchased_at: datetime
    created_by: UUID
    created_at: datetime


class InventoryMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    movement_type: InventoryMovementType
    quantity_change: Decimal
    stock_before: Decimal
    stock_after: Decimal
    unit_cost: Decimal | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime


class LowStockIngredientRead(IngredientRead):
    pass
