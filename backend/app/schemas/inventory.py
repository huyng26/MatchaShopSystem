from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator


class IngredientBase(BaseModel):
    name: str
    unit: str
    cost_per_unit: Decimal
    min_stock_threshold: Decimal = Decimal("0")


class IngredientCreate(IngredientBase):
    current_stock: Decimal = Decimal("0")


class IngredientUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    cost_per_unit: Decimal | None = None
    min_stock_threshold: Decimal | None = None


class IngredientResponse(IngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_stock: Decimal
    created_at: datetime
    updated_at: datetime


# --- Purchases ---

class IngredientPurchaseBase(BaseModel):
    ingredient_id: int
    quantity: Decimal
    unit_cost: Decimal
    supplier: str | None = None
    notes: str | None = None

    @field_validator("quantity", "unit_cost")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Must be greater than zero")
        return v


class IngredientPurchaseCreate(IngredientPurchaseBase):
    pass


class IngredientPurchaseResponse(IngredientPurchaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_cost: Decimal
    purchased_at: datetime
