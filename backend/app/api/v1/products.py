import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.integration_contracts import Actor, require_roles
from app.schemas.product import (
    ProductAvailabilityUpdate,
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryUpdate,
    ProductCreate,
    ProductRecipeResponse,
    ProductRecipeUpdate,
    ProductResponse,
    ProductUpdate,
)
from app.services import product_service

router = APIRouter()
product_read = require_roles("admin", "inventory_manager", "delivery_manager", "cashier")
product_write = require_roles("admin", "inventory_manager")


@router.get("/categories", response_model=list[ProductCategoryResponse])
async def list_categories(
    _: Actor = Depends(product_read),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.list_categories(db)


@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: ProductCategoryCreate,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.create_category(db, data)


@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    data: ProductCategoryUpdate,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.update_category(db, category_id, data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    await product_service.delete_category(db, category_id)


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    available_only: bool = False,
    actor: Actor = Depends(product_read),
    db: AsyncSession = Depends(get_db),
):
    must_hide_unavailable = actor.role in {"cashier", "delivery_manager"}
    return await product_service.list_products(db, skip, limit, available_only or must_hide_unavailable)


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.create_product(db, data)


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    _: Actor = Depends(product_read),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.get_product(db, product_id)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.update_product(db, product_id, data)


@router.patch("/products/{product_id}/availability", response_model=ProductResponse)
async def update_availability(
    product_id: uuid.UUID,
    data: ProductAvailabilityUpdate,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.update_availability(db, product_id, data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    actor: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    await product_service.delete_product(db, product_id, actor.user_id)


@router.get("/products/{product_id}/recipe", response_model=list[ProductRecipeResponse])
async def get_recipe(
    product_id: uuid.UUID,
    _: Actor = Depends(product_read),
    db: AsyncSession = Depends(get_db),
):
    return (await product_service.get_product(db, product_id)).recipes


@router.put("/products/{product_id}/recipe", response_model=ProductResponse)
async def replace_recipe(
    product_id: uuid.UUID,
    data: ProductRecipeUpdate,
    _: Actor = Depends(product_write),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.replace_recipe(db, product_id, data.ingredients)
