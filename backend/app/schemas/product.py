from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ProductIngredientBase(BaseModel):
    ingredient_id: int
    quantity_required: Decimal


class ProductIngredientCreate(ProductIngredientBase):
    pass


class ProductIngredientResponse(ProductIngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_name: str | None = None


class ProductBase(BaseModel):
    name: str
    category: str
    description: str | None = None
    selling_price: Decimal
    is_available: bool = True


class ProductCreate(ProductBase):
    ingredients: list[ProductIngredientCreate] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    selling_price: Decimal | None = None
    is_available: bool | None = None
    ingredients: list[ProductIngredientCreate] | None = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredients: list[ProductIngredientResponse] = []
    created_at: datetime
    updated_at: datetime
