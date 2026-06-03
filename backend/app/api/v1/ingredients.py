from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with inventory_service calls when implementing real APIs.
MOCK_INGREDIENTS = [
    {
        "id": "ingredient-matcha-powder",
        "name": "Matcha powder",
        "unit": "g",
        "current_stock": 850,
        "cost_per_unit": 1200,
        "minimum_threshold": 500,
    },
    {
        "id": "ingredient-milk",
        "name": "Fresh milk",
        "unit": "ml",
        "current_stock": 3200,
        "cost_per_unit": 35,
        "minimum_threshold": 5000,
    },
]


@router.get("")
async def list_ingredients() -> dict[str, Any]:
    return success_response(data=MOCK_INGREDIENTS)


@router.get("/low-stock")
async def list_low_stock_ingredients() -> dict[str, Any]:
    low_stock = [
        item
        for item in MOCK_INGREDIENTS
        if item["current_stock"] <= item["minimum_threshold"]
    ]
    return success_response(data=low_stock)
