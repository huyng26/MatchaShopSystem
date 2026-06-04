from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.responses import success_response
from app.models.user import User
from app.schemas.common import to_jsonable
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.order import OrderRead
from app.services import customer_service

router = APIRouter()

CustomerManager = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN, UserRole.CASHIER)),
]


@router.get("")
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CustomerManager,
    q: Annotated[str | None, Query(max_length=255)] = None,
) -> dict:
    customers = await customer_service.list_customers(db, search=q)
    return success_response(
        data=to_jsonable(
            [CustomerResponse.model_validate(customer) for customer in customers]
        )
    )


@router.post("")
async def create_customer(
    payload: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CustomerManager,
) -> dict:
    customer = await customer_service.create_customer(db, payload)
    return success_response(
        message="Customer created successfully",
        data=to_jsonable(CustomerResponse.model_validate(customer)),
    )


@router.get("/{customer_id}")
async def get_customer(
    customer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CustomerManager,
) -> dict:
    customer = await customer_service.get_customer(db, customer_id)
    return success_response(data=to_jsonable(CustomerResponse.model_validate(customer)))


@router.put("/{customer_id}")
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CustomerManager,
) -> dict:
    customer = await customer_service.update_customer(db, customer_id, payload)
    return success_response(
        message="Customer updated successfully",
        data=to_jsonable(CustomerResponse.model_validate(customer)),
    )


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CustomerManager,
) -> dict:
    customer = await customer_service.delete_customer(db, customer_id)
    return success_response(
        message="Customer deleted successfully",
        data=to_jsonable(CustomerResponse.model_validate(customer)),
    )


@router.get("/{customer_id}/orders")
async def get_customer_orders(
    customer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CustomerManager,
) -> dict:
    orders = await customer_service.list_customer_orders(db, customer_id)
    return success_response(
        data=to_jsonable([OrderRead.model_validate(order) for order in orders])
    )
