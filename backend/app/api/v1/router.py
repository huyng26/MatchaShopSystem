from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    auth,
    customers,
    dashboard,
    deliveries,
    finance,
    ingredients,
    inventory,
    orders,
    payments,
    products,
    staff,
    status,
)


api_router = APIRouter()
api_router.include_router(status.router, tags=["status"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(
    ingredients.router,
    prefix="/ingredients",
    tags=["ingredients"],
)
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(
    deliveries.router,
    prefix="/deliveries",
    tags=["deliveries"],
)
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
)
