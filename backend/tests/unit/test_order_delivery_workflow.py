from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.order import OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import PaymentEventStatus, PaymentMethod
from app.schemas.order import OrderReadyForDelivery
from app.services import order_service
from app.services.errors import ServiceError


class FakeDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.refreshes = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def flush(self) -> None:
        self.flushes += 1

    async def refresh(self, obj) -> None:
        self.refreshes += 1


def make_order(
    *,
    status: OrderStatus = OrderStatus.IN_PROGRESS,
    payment_status: OrderPaymentStatus = OrderPaymentStatus.UNPAID,
    customer_name: str | None = "Tran Binh",
    customer_phone: str | None = "0987654321",
    delivery_address: str | None = "Quan 3, TP.HCM",
    delivery_latitude: Decimal | None = Decimal("10.7829000"),
    delivery_longitude: Decimal | None = Decimal("106.6934000"),
    payments=None,
):
    return SimpleNamespace(
        id=uuid4(),
        order_code="ORD-READY",
        customer_id=None,
        order_type=OrderType.DELIVERY,
        status=status,
        payment_status=payment_status,
        subtotal=Decimal("65000.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("65000.00"),
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_address=delivery_address,
        delivery_latitude=delivery_latitude,
        delivery_longitude=delivery_longitude,
        note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        completed_at=None,
        cancelled_at=None,
        payments=payments or [],
        items=[],
    )


@pytest.mark.asyncio
async def test_ready_for_delivery_rejects_missing_delivery_fields(monkeypatch):
    db = FakeDb()
    order = make_order(delivery_latitude=None)

    async def get_order_detail(db, order_id):
        return order

    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)

    with pytest.raises(ServiceError) as error:
        await order_service.mark_ready_for_delivery(
            db,
            order.id,
            OrderReadyForDelivery(),
            actor_user_id=uuid4(),
        )

    assert error.value.code == "delivery_fields_required"
    assert error.value.status_code == 422
    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_ready_for_delivery_unpaid_requires_cod(monkeypatch):
    db = FakeDb()
    order = make_order()

    async def get_order_detail(db, order_id):
        return order

    async def order_has_active_assignment(db, order_id):
        return False

    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)
    monkeypatch.setattr(
        order_service.delivery_repo,
        "order_has_active_assignment",
        order_has_active_assignment,
    )

    with pytest.raises(ServiceError) as error:
        await order_service.mark_ready_for_delivery(
            db,
            order.id,
            OrderReadyForDelivery(),
            actor_user_id=uuid4(),
        )

    assert error.value.code == "cod_payment_required_for_unpaid_delivery"
    assert error.value.status_code == 409
    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_ready_for_delivery_creates_cod_pending(monkeypatch):
    db = FakeDb()
    order = make_order()
    captured = {}

    async def get_order_detail(db, order_id):
        return order

    async def order_has_active_assignment(db, order_id):
        return False

    async def get_pending_cod_payment_for_order(db, order_id):
        return None

    async def create_payment_event(db, **kwargs):
        captured["payment"] = kwargs
        payment = SimpleNamespace(id=uuid4(), **kwargs)
        order.payments.append(payment)
        return payment

    async def update_order_status(db, order, *, status=None, payment_status=None):
        if status is not None:
            order.status = status
        if payment_status is not None:
            order.payment_status = payment_status
        return order

    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)
    monkeypatch.setattr(
        order_service.delivery_repo,
        "order_has_active_assignment",
        order_has_active_assignment,
    )
    monkeypatch.setattr(
        order_service.payment_repo,
        "get_pending_cod_payment_for_order",
        get_pending_cod_payment_for_order,
    )
    monkeypatch.setattr(
        order_service.payment_repo,
        "create_payment_event",
        create_payment_event,
    )
    monkeypatch.setattr(
        order_service.order_repo,
        "update_order_status",
        update_order_status,
    )

    result = await order_service.mark_ready_for_delivery(
        db,
        order.id,
        OrderReadyForDelivery(payment_method=PaymentMethod.COD),
        actor_user_id=uuid4(),
    )

    assert result.status == OrderStatus.READY_FOR_DELIVERY
    assert captured["payment"]["method"] == PaymentMethod.COD
    assert captured["payment"]["status"] == PaymentEventStatus.PENDING
    assert captured["payment"]["amount"] == Decimal("65000.00")
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_ready_for_delivery_accepts_successful_prepaid(monkeypatch):
    db = FakeDb()
    order = make_order(
        payment_status=OrderPaymentStatus.PAID,
        payments=[
            SimpleNamespace(
                method=PaymentMethod.BANK_TRANSFER,
                status=PaymentEventStatus.SUCCESS,
            )
        ],
    )

    async def get_order_detail(db, order_id):
        return order

    async def order_has_active_assignment(db, order_id):
        return False

    async def update_order_status(db, order, *, status=None, payment_status=None):
        if status is not None:
            order.status = status
        if payment_status is not None:
            order.payment_status = payment_status
        return order

    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)
    monkeypatch.setattr(
        order_service.delivery_repo,
        "order_has_active_assignment",
        order_has_active_assignment,
    )
    monkeypatch.setattr(
        order_service.order_repo,
        "update_order_status",
        update_order_status,
    )

    result = await order_service.mark_ready_for_delivery(
        db,
        order.id,
        OrderReadyForDelivery(),
        actor_user_id=uuid4(),
    )

    assert result.status == OrderStatus.READY_FOR_DELIVERY
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_ready_for_delivery_rejects_paid_cash_delivery(monkeypatch):
    db = FakeDb()
    order = make_order(
        payment_status=OrderPaymentStatus.PAID,
        payments=[
            SimpleNamespace(
                method=PaymentMethod.CASH,
                status=PaymentEventStatus.SUCCESS,
            )
        ],
    )

    async def get_order_detail(db, order_id):
        return order

    async def order_has_active_assignment(db, order_id):
        return False

    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)
    monkeypatch.setattr(
        order_service.delivery_repo,
        "order_has_active_assignment",
        order_has_active_assignment,
    )

    with pytest.raises(ServiceError) as error:
        await order_service.mark_ready_for_delivery(
            db,
            order.id,
            OrderReadyForDelivery(),
            actor_user_id=uuid4(),
        )

    assert error.value.code == "delivery_prepaid_payment_required"
    assert error.value.status_code == 409
