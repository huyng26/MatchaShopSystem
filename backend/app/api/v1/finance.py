from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import created, ok, raise_service_error, read_list, read_one
from app.core.constants import UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.user import User
from app.schemas.finance import (
    ExpenseCreate,
    ExpenseRead,
    FinanceSummaryRead,
    FinancialRecordRead,
)
from app.services import finance_service
from app.services.errors import ServiceError

router = APIRouter()

FinanceUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)),
]


@router.get("/summary")
async def get_finance_summary(
    _current_user: FinanceUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str,
) -> dict[str, Any]:
    try:
        summary = await finance_service.get_finance_summary(db, month=month)
        return ok(FinanceSummaryRead.model_validate(summary))
    except ServiceError as error:
        raise_service_error(error)


@router.get("/expenses")
async def list_expenses(
    _current_user: FinanceUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str,
) -> dict[str, Any]:
    try:
        expenses = await finance_service.list_expenses(db, month=month)
        return ok(read_list(ExpenseRead, expenses))
    except ServiceError as error:
        raise_service_error(error)


@router.post("/expenses")
async def create_expense(
    payload: ExpenseCreate,
    current_user: FinanceUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    try:
        expense = await finance_service.create_expense(
            db,
            payload,
            created_by=current_user.id,
        )
        return created(
            read_one(ExpenseRead, expense),
            message="Expense created successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.get("/records")
async def list_financial_records(
    _current_user: FinanceUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str,
) -> dict[str, Any]:
    try:
        records = await finance_service.list_financial_records(db, month=month)
        return ok(read_list(FinancialRecordRead, records))
    except ServiceError as error:
        raise_service_error(error)
