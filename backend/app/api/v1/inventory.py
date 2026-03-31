from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import inventory as crud
from app.schemas.inventory import (
    IngredientCreate,
    IngredientUpdate,
    IngredientResponse,
    IngredientPurchaseCreate,
    IngredientPurchaseResponse,
)
from app.services.inventory_service import get_low_stock_ingredients

router = APIRouter()


@router.get("/ingredients", response_model=list[IngredientResponse])
async def list_ingredients(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_ingredients(db, skip=skip, limit=limit)


@router.post("/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient(data: IngredientCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_ingredient(db, data)


@router.get("/ingredients/low-stock", response_model=list[IngredientResponse])
async def low_stock(db: AsyncSession = Depends(get_db)):
    return await get_low_stock_ingredients(db)


@router.get("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(ingredient_id: int, db: AsyncSession = Depends(get_db)):
    ingredient = await crud.get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


@router.patch("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(ingredient_id: int, data: IngredientUpdate, db: AsyncSession = Depends(get_db)):
    ingredient = await crud.get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return await crud.update_ingredient(db, ingredient, data)


@router.delete("/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(ingredient_id: int, db: AsyncSession = Depends(get_db)):
    ingredient = await crud.get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    await crud.delete_ingredient(db, ingredient)


# --- Purchases ---

@router.get("/purchases", response_model=list[IngredientPurchaseResponse])
async def list_purchases(
    ingredient_id: int | None = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    return await crud.get_purchases(db, ingredient_id=ingredient_id, skip=skip, limit=limit)


@router.post("/purchases", response_model=IngredientPurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase(data: IngredientPurchaseCreate, db: AsyncSession = Depends(get_db)):
    ingredient = await crud.get_ingredient(db, data.ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return await crud.create_purchase(db, data)
