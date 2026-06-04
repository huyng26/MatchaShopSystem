from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProductCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None


class ProductCreate(BaseModel):
    category_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    selling_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    is_available: bool = True


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    selling_price: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    is_available: bool | None = None


class ProductAvailabilityUpdate(BaseModel):
    is_available: bool


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    name: str
    description: str | None = None
    selling_price: Decimal
    is_available: bool


class RecipeItemCreate(BaseModel):
    ingredient_id: UUID
    quantity_per_serving: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3)


class RecipeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: UUID
    ingredient_name: str | None = None
    unit: str | None = None
    quantity_per_serving: Decimal

    @model_validator(mode="before")
    @classmethod
    def populate_ingredient_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        ingredient = getattr(data, "ingredient", None)
        return {
            "ingredient_id": getattr(data, "ingredient_id", None),
            "ingredient_name": getattr(ingredient, "name", None),
            "unit": getattr(ingredient, "unit", None),
            "quantity_per_serving": getattr(data, "quantity_per_serving", None),
        }


class ProductRecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    items: list[RecipeItemRead]

    @model_validator(mode="before")
    @classmethod
    def populate_recipe_items(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        return {
            "product_id": getattr(data, "id", getattr(data, "product_id", None)),
            "items": getattr(data, "recipe_rows", getattr(data, "items", [])),
        }


class ProductRecipeUpdate(BaseModel):
    items: list[RecipeItemCreate] = Field(..., min_length=1)
