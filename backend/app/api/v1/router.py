from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    auth,
    customers,
    dashboard,
    deliveries,
    finance,
    ingredients,
    orders,
    payments,
    products,
    staff,
    status,
)


api_router = APIRouter()
api_router.include_router(status.router, tags=["status"])
api_router.include_router(auth.router, prefix="/auth", tags=["mock-auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["mock-accounts"])
api_router.include_router(staff.router, prefix="/staff", tags=["mock-staff"])
api_router.include_router(customers.router, prefix="/customers", tags=["mock-customers"])
api_router.include_router(products.router, prefix="/products", tags=["mock-products"])
api_router.include_router(
    ingredients.router,
    prefix="/ingredients",
    tags=["mock-ingredients"],
)
api_router.include_router(orders.router, prefix="/orders", tags=["mock-orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["mock-payments"])
api_router.include_router(
    deliveries.router,
    prefix="/deliveries",
    tags=["mock-deliveries"],
)
api_router.include_router(finance.router, prefix="/finance", tags=["mock-finance"])
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["mock-dashboard"],
)
