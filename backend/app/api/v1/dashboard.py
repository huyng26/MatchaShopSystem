from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with dashboard_service calls when implementing real APIs.
MOCK_DASHBOARD_TODAY = {
    "date": "2026-06-01",
    "revenue": 55000,
    "order_count": 2,
    "completed_order_count": 1,
    "delivery_queue_count": 1,
    "low_stock_count": 1,
}

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

MOCK_PRODUCTS = [
    {
        "id": "product-matcha-latte",
        "name": "Matcha Latte",
        "selling_price": 55000,
    },
    {
        "id": "product-matcha-frappe",
        "name": "Matcha Frappe",
        "selling_price": 65000,
    },
]


@router.get("/today")
async def get_today_dashboard() -> dict[str, Any]:
    return success_response(data=MOCK_DASHBOARD_TODAY)


@router.get("/low-stock")
async def get_low_stock_dashboard() -> dict[str, Any]:
    low_stock = [
        item
        for item in MOCK_INGREDIENTS
        # pyrefly: ignore [unsupported-operation]
        if item["current_stock"] <= item["minimum_threshold"]
    ]
    return success_response(data=low_stock)


@router.get("/best-selling-products")
async def get_best_selling_products() -> dict[str, Any]:
    return success_response(
        data=[
            {"product": MOCK_PRODUCTS[0], "quantity_sold": 24, "revenue": 1320000},
            {"product": MOCK_PRODUCTS[1], "quantity_sold": 16, "revenue": 1040000},
        ]
    )


@router.get("/delivery-performance")
async def get_delivery_performance() -> dict[str, Any]:
    return success_response(
        data={
            "total_trips": 1,
            "completed_trips": 0,
            "average_delivery_minutes": 0,
            "cod_pending": 65000,
        }
    )
