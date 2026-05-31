from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProductCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ProductRecipeItem(BaseModel):
    ingredient_id: uuid.UUID
    quantity_per_serving: Decimal = Field(gt=0)


class ProductRecipeUpdate(BaseModel):
    ingredients: list[ProductRecipeItem]

    @model_validator(mode="after")
    def reject_duplicate_ingredients(self) -> "ProductRecipeUpdate":
        ingredient_ids = [item.ingredient_id for item in self.ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValueError("Recipe ingredients must be unique")
        return self


class ProductRecipeResponse(ProductRecipeItem):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    selling_price: Decimal = Field(gt=0)
    is_available: bool = True
    ingredients: list[ProductRecipeItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_ingredients(self) -> "ProductCreate":
        ProductRecipeUpdate(ingredients=self.ingredients)
        return self


class ProductUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    selling_price: Decimal | None = Field(default=None, gt=0)
    is_available: bool | None = None


class ProductAvailabilityUpdate(BaseModel):
    is_available: bool


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: str | None
    selling_price: Decimal
    is_available: bool
    recipes: list[ProductRecipeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
