from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.schema import Column

from app.models.base import Base
from app.models.user import enum_values


class FinancialRecordType(str, Enum):
    REVENUE = "revenue"
    MATERIAL_COST = "material_cost"
    OPERATING_EXPENSE = "operating_expense"
    COD_RECONCILIATION = "cod_reconciliation"
    REFUND = "refund"


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="expenses_amount_positive"),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    expense_month = Column(Date, nullable=False)
    invoice_photo_url = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at = Column(DateTime(timezone=True))


class FinancialRecord(Base):
    __tablename__ = "financial_records"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="financial_records_amount_non_negative"),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    record_type = Column(
        SQLEnum(
            FinancialRecordType,
            name="financial_record_type",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    source_type = Column(String(100), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    record_date = Column(Date, nullable=False)
    locked = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
