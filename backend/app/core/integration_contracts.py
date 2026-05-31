from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession


class SharedContractUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Actor:
    user_id: uuid.UUID
    role: str


RoleChecker = Callable[[Request, frozenset[str]], Awaitable[Actor]]
AuditWriter = Callable[
    [AsyncSession, uuid.UUID | None, str, str, uuid.UUID | None, dict[str, Any] | None],
    Awaitable[None],
]
FinancialRecordWriter = Callable[
    [AsyncSession, str, str, uuid.UUID, Decimal, date],
    Awaitable[None],
]

_role_checker: RoleChecker | None = None
_audit_writer: AuditWriter | None = None
_financial_record_writer: FinancialRecordWriter | None = None


def register_role_checker(checker: RoleChecker) -> None:
    global _role_checker
    _role_checker = checker


def register_audit_writer(writer: AuditWriter) -> None:
    global _audit_writer
    _audit_writer = writer


def register_financial_record_writer(writer: FinancialRecordWriter) -> None:
    global _financial_record_writer
    _financial_record_writer = writer


def require_roles(*roles: str):
    allowed_roles = frozenset(roles)

    async def dependency(request: Request) -> Actor:
        if _role_checker is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RBAC integration is not registered",
            )
        return await _role_checker(request, allowed_roles)

    return dependency


async def write_audit(
    db: AsyncSession,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    new_value: dict[str, Any] | None = None,
) -> None:
    if _audit_writer is None:
        raise SharedContractUnavailable("Audit integration is not registered")
    await _audit_writer(db, actor_user_id, action, entity_type, entity_id, new_value)


async def write_financial_record(
    db: AsyncSession,
    record_type: str,
    source_type: str,
    source_id: uuid.UUID,
    amount: Decimal,
    record_date: date,
) -> None:
    if _financial_record_writer is None:
        raise SharedContractUnavailable("Financial record integration is not registered")
    await _financial_record_writer(db, record_type, source_type, source_id, amount, record_date)
