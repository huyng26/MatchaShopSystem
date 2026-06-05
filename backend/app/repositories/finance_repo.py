from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, FinancialRecord, FinancialRecordType


async def create_expense(
    db: AsyncSession,
    *,
    category: str,
    description: str,
    amount: Decimal,
    expense_month: date,
    created_by: UUID,
    invoice_photo_url: str | None = None,
) -> Expense:
    expense = Expense(
        category=category,
        description=description,
        amount=amount,
        expense_month=expense_month,
        invoice_photo_url=invoice_photo_url,
        created_by=created_by,
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return expense


async def list_expenses_by_month(
    db: AsyncSession,
    *,
    month_start: date,
    next_month_start: date,
) -> Sequence[Expense]:
    stmt = (
        select(Expense)
        .where(
            Expense.deleted_at.is_(None),
            Expense.expense_month >= month_start,
            Expense.expense_month < next_month_start,
        )
        .order_by(Expense.expense_month.desc(), Expense.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_expense_by_category_and_month(
    db: AsyncSession,
    *,
    category: str,
    expense_month: date,
) -> Expense | None:
    stmt = select(Expense).where(
        Expense.category == category,
        Expense.expense_month == expense_month,
        Expense.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


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
    record = FinancialRecord(
        record_type=record_type,
        source_type=source_type,
        source_id=source_id,
        amount=amount,
        record_date=record_date,
        locked=locked,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def list_financial_records_by_source(
    db: AsyncSession,
    *,
    source_type: str,
    source_id: UUID,
) -> Sequence[FinancialRecord]:
    stmt = (
        select(FinancialRecord)
        .where(
            FinancialRecord.source_type == source_type,
            FinancialRecord.source_id == source_id,
        )
        .order_by(FinancialRecord.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def list_financial_records_by_month(
    db: AsyncSession,
    *,
    month_start: date,
    next_month_start: date,
) -> Sequence[FinancialRecord]:
    stmt = (
        select(FinancialRecord)
        .where(
            FinancialRecord.record_date >= month_start,
            FinancialRecord.record_date < next_month_start,
        )
        .order_by(FinancialRecord.record_date.desc(), FinancialRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_monthly_totals(
    db: AsyncSession,
    *,
    month_start: date,
    next_month_start: date,
) -> dict[FinancialRecordType, Decimal]:
    stmt = (
        select(
            FinancialRecord.record_type,
            func.coalesce(func.sum(FinancialRecord.amount), Decimal("0")).label(
                "total"
            ),
        )
        .where(
            FinancialRecord.record_date >= month_start,
            FinancialRecord.record_date < next_month_start,
        )
        .group_by(FinancialRecord.record_type)
    )
    result = await db.execute(stmt)
    return {record_type: total for record_type, total in result.all()}


async def financial_record_exists(
    db: AsyncSession,
    *,
    record_type: FinancialRecordType,
    source_type: str,
    source_id: UUID,
) -> bool:
    stmt = select(
        exists().where(
            FinancialRecord.record_type == record_type,
            FinancialRecord.source_type == source_type,
            FinancialRecord.source_id == source_id,
        )
    )
    result = await db.execute(stmt)
    return bool(result.scalar())


async def completion_record_exists(
    db: AsyncSession,
    *,
    source_type: str,
    source_id: UUID,
    record_type: FinancialRecordType = FinancialRecordType.REVENUE,
) -> bool:
    return await financial_record_exists(
        db,
        record_type=record_type,
        source_type=source_type,
        source_id=source_id,
    )
