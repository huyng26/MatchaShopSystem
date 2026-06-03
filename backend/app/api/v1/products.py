from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with product_service calls when implementing real APIs.
MOCK_PRODUCT_CATEGORIES = [
    {"id": "category-matcha", "name": "Matcha", "description": "Matcha drinks"},
    {"id": "category-tea", "name": "Tea", "description": "Tea drinks"},
]

MOCK_PRODUCTS = [
    {
        "id": "product-matcha-latte",
        "category_id": "category-matcha",
        "name": "Matcha Latte",
        "description": "Classic matcha latte",
        "selling_price": 55000,
        "is_available": True,
    },
    {
        "id": "product-matcha-frappe",
        "category_id": "category-matcha",
        "name": "Matcha Frappe",
        "description": "Blended iced matcha",
        "selling_price": 65000,
        "is_available": True,
    },
]


@router.get("")
async def list_products() -> dict[str, Any]:
    return success_response(data=MOCK_PRODUCTS)


@router.get("/categories")
async def list_categories() -> dict[str, Any]:
    return success_response(data=MOCK_PRODUCT_CATEGORIES)


@router.get("/{product_id}")
async def get_product(product_id: str) -> dict[str, Any]:
    product = next((item for item in MOCK_PRODUCTS if item["id"] == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="product_not_found")
    return success_response(data=product)
