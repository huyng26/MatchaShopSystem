from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinancialRecord, FinancialRecordType
from app.repositories import finance_repo


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
