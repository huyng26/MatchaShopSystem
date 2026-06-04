from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinancialRecord, FinancialRecordType


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
