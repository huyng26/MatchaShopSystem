import re
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, FinancialRecord, FinancialRecordType
from app.repositories import finance_repo, staff_repo
from app.schemas.finance import (
    ExpenseCreate,
    ExpenseRead,
    FinanceSummaryRead,
    StaffWageExpenseRead,
)
from app.services.errors import ServiceError

MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
STAFF_WAGE_CATEGORY = "staff_wage"


async def create_financial_record(
    db: AsyncSession,
    *,
    record_type: FinancialRecordType,
    source_type: str,
    source_id: UUID,
    amount: Decimal,
    record_date: date,
    locked: bool = False,
) -> FinancialRecord:
    try:
        record = await finance_repo.create_financial_record(
            db,
            record_type=record_type,
            source_type=source_type,
            source_id=source_id,
            amount=amount,
            record_date=record_date,
            locked=locked,
        )
        await db.commit()
        return record
    except Exception:
        await db.rollback()
        raise


async def list_financial_records_by_source(
    db: AsyncSession,
    *,
    source_type: str,
    source_id: UUID,
) -> Sequence[FinancialRecord]:
    return await finance_repo.list_financial_records_by_source(
        db,
        source_type=source_type,
        source_id=source_id,
    )


async def create_staff_wage_expense(
    db: AsyncSession,
    *,
    month: str,
    created_by: UUID,
) -> StaffWageExpenseRead:
    month_start, _next_month_start = parse_month(month)
    existing = await finance_repo.get_expense_by_category_and_month(
        db,
        category=STAFF_WAGE_CATEGORY,
        expense_month=month_start,
    )
    if existing is not None:
        raise ServiceError("staff_wage_expense_already_exists", status_code=409)

    total_salary, staff_count = await staff_repo.sum_active_staff_salaries(db)
    if total_salary <= Decimal("0"):
        raise ServiceError("staff_wage_total_is_zero")

    try:
        expense = await finance_repo.create_expense(
            db,
            category=STAFF_WAGE_CATEGORY,
            description=f"Staff wages for {month}",
            amount=total_salary,
            expense_month=month_start,
            invoice_photo_url=None,
            created_by=created_by,
        )
        await finance_repo.create_financial_record(
            db,
            record_type=FinancialRecordType.OPERATING_EXPENSE,
            source_type="expense",
            source_id=expense.id,
            amount=expense.amount,
            record_date=expense.expense_month,
            locked=False,
        )
        await db.commit()
        return StaffWageExpenseRead(
            expense=ExpenseRead.model_validate(expense),
            staff_count=staff_count,
            total_salary=total_salary,
        )
    except Exception:
        await db.rollback()
        raise


async def create_expense(
    db: AsyncSession,
    payload: ExpenseCreate,
    *,
    created_by: UUID,
) -> Expense:
    if payload.amount <= Decimal("0"):
        raise ServiceError("expense_amount_must_be_positive")

    try:
        expense = await finance_repo.create_expense(
            db,
            category=payload.category,
            description=payload.description,
            amount=payload.amount,
            expense_month=payload.expense_month,
            invoice_photo_url=payload.invoice_photo_url,
            created_by=created_by,
        )
        await finance_repo.create_financial_record(
            db,
            record_type=FinancialRecordType.OPERATING_EXPENSE,
            source_type="expense",
            source_id=expense.id,
            amount=expense.amount,
            record_date=expense.expense_month,
            locked=False,
        )
        await db.commit()
        return expense
    except Exception:
        await db.rollback()
        raise


async def list_expenses(
    db: AsyncSession,
    *,
    month: str,
) -> Sequence[Expense]:
    month_start, next_month_start = parse_month(month)
    return await finance_repo.list_expenses_by_month(
        db,
        month_start=month_start,
        next_month_start=next_month_start,
    )


async def list_financial_records(
    db: AsyncSession,
    *,
    month: str,
) -> Sequence[FinancialRecord]:
    month_start, next_month_start = parse_month(month)
    return await finance_repo.list_financial_records_by_month(
        db,
        month_start=month_start,
        next_month_start=next_month_start,
    )


async def get_finance_summary(
    db: AsyncSession,
    *,
    month: str,
) -> FinanceSummaryRead:
    month_start, next_month_start = parse_month(month)
    totals = await finance_repo.get_monthly_totals(
        db,
        month_start=month_start,
        next_month_start=next_month_start,
    )
    revenue = _total(totals, FinancialRecordType.REVENUE)
    material_cost = _total(totals, FinancialRecordType.MATERIAL_COST)
    operating_expense = _total(totals, FinancialRecordType.OPERATING_EXPENSE)
    return FinanceSummaryRead(
        revenue=revenue,
        material_cost=material_cost,
        operating_expense=operating_expense,
        net_profit=revenue - material_cost - operating_expense,
    )


def parse_month(month: str) -> tuple[date, date]:
    if not MONTH_PATTERN.fullmatch(month):
        raise ServiceError("month_must_use_yyyy_mm_format")

    year = int(month[:4])
    month_number = int(month[5:7])
    if month_number < 1 or month_number > 12:
        raise ServiceError("month_must_use_yyyy_mm_format")

    month_start = date(year, month_number, 1)
    if month_number == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month_number + 1, 1)
    return month_start, next_month_start


def _total(
    totals: dict[FinancialRecordType, Decimal],
    record_type: FinancialRecordType,
) -> Decimal:
    return totals.get(record_type, Decimal("0"))
