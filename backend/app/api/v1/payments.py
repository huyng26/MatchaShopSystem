import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.integration_contracts import Actor, require_roles
from app.schemas.payment import (
    BankTransferVerification,
    CardPaymentCreate,
    CashPaymentCreate,
    PaymentResponse,
)
from app.services import payment_service

router = APIRouter()
payment_read = require_roles("admin", "cashier", "delivery_manager")
payment_write = require_roles("admin", "cashier")


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    _: Actor = Depends(payment_read),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.get_payment(db, payment_id)


@router.get("/orders/{order_id}/payments", response_model=list[PaymentResponse])
async def list_order_payments(
    order_id: uuid.UUID,
    _: Actor = Depends(payment_read),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.list_order_payments(db, order_id)


@router.post(
    "/orders/{order_id}/payments/cash",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_cash_payment(
    order_id: uuid.UUID,
    data: CashPaymentCreate,
    actor: Actor = Depends(payment_write),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.record_cash_payment(db, order_id, data, actor.user_id)


@router.post(
    "/orders/{order_id}/payments/card",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_card_payment(
    order_id: uuid.UUID,
    data: CardPaymentCreate,
    actor: Actor = Depends(payment_write),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.record_card_payment(db, order_id, data, actor.user_id)


@router.post(
    "/orders/{order_id}/payments/bank-transfer",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bank_transfer(
    order_id: uuid.UUID,
    actor: Actor = Depends(payment_write),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.create_bank_transfer(db, order_id, actor.user_id)


@router.post("/payments/{payment_id}/verify-bank-transfer", response_model=PaymentResponse)
async def verify_bank_transfer(
    payment_id: uuid.UUID,
    data: BankTransferVerification,
    actor: Actor = Depends(payment_write),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.verify_bank_transfer(db, payment_id, data, actor.user_id)


@router.post(
    "/orders/{order_id}/payments/cod",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cod_payment(
    order_id: uuid.UUID,
    actor: Actor = Depends(payment_write),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.create_cod_payment(db, order_id, actor.user_id)
