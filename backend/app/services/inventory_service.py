"""
Inventory service: stock deduction when orders are placed.
"""
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import inventory as inventory_crud
from app.models.product import ProductIngredient


async def deduct_stock_for_order_items(
    db: AsyncSession, order_items: list[tuple[ProductIngredient, int]]
) -> None:
    """
    Deduct ingredient stock for each (recipe_line, quantity) pair.
    order_items: list of (ProductIngredient, order_quantity)
    """
    for recipe_line, quantity in order_items:
        delta = Decimal(str(recipe_line.quantity_required)) * quantity
        ingredient = await inventory_crud.get_ingredient(db, recipe_line.ingredient_id)
        if ingredient:
            await inventory_crud.adjust_stock(db, ingredient, -delta)


async def get_low_stock_ingredients(db: AsyncSession) -> list:
    """Return ingredients where current_stock <= min_stock_threshold."""
    ingredients = await inventory_crud.get_ingredients(db, limit=1000)
    return [i for i in ingredients if i.current_stock <= i.min_stock_threshold]
