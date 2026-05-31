from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.ingredient import InventoryMovementType


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    unit: str = Field(min_length=1, max_length=50)
    cost_per_unit: Decimal = Field(ge=0)
    minimum_threshold: Decimal = Field(default=Decimal("0"), ge=0)


class IngredientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    cost_per_unit: Decimal | None = Field(default=None, ge=0)
    minimum_threshold: Decimal | None = Field(default=None, ge=0)


class IngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    unit: str
    current_stock: Decimal
    cost_per_unit: Decimal
    minimum_threshold: Decimal
    created_at: datetime
    updated_at: datetime


class InventoryPurchaseCreate(BaseModel):
    quantity: Decimal = Field(gt=0)
    cost_per_unit: Decimal = Field(ge=0)
    supplier_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class InventoryPurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ingredient_id: uuid.UUID
    quantity: Decimal
    cost_per_unit: Decimal
    total_cost: Decimal
    supplier_name: str | None
    notes: str | None
    purchased_at: datetime
    created_by: uuid.UUID


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ingredient_id: uuid.UUID
    movement_type: InventoryMovementType
    quantity_change: Decimal
    stock_before: Decimal
    stock_after: Decimal
    unit_cost: Decimal | None
    reference_type: str | None
    reference_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime
