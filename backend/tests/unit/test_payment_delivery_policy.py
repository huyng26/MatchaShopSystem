from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.order import OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import PaymentEventStatus, PaymentMethod
from app.schemas.payment import PaymentCreate
from app.services import payment_service
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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def make_order(*, order_type: OrderType = OrderType.DELIVERY):
    return SimpleNamespace(
        id=uuid4(),
        order_type=order_type,
        payment_status=OrderPaymentStatus.UNPAID,
        total_amount=Decimal("65000.00"),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.anyio
async def test_cod_delivery_payment_is_pending_and_does_not_mark_paid(monkeypatch):
    db = FakeDb()
    order = make_order(order_type=OrderType.DELIVERY)
    captured = {}

    async def get_order(db, order_id):
        return order

    async def get_pending_cod_payment_for_order(db, order_id):
        return None

    async def create_payment_event(db, **kwargs):
        captured["payment"] = kwargs
        return SimpleNamespace(id=uuid4(), **kwargs)

    async def update_order_status(db, order, *, status=None, payment_status=None):
        captured["updated_status"] = payment_status
        return order

    monkeypatch.setattr(payment_service.order_repo, "get_order", get_order)
    monkeypatch.setattr(
        payment_service.payment_repo,
        "get_pending_cod_payment_for_order",
        get_pending_cod_payment_for_order,
    )
    monkeypatch.setattr(
        payment_service.payment_repo,
        "create_payment_event",
        create_payment_event,
    )
    monkeypatch.setattr(
        payment_service.order_repo,
        "update_order_status",
        update_order_status,
    )

    payment = await payment_service.create_payment(
        db,
        PaymentCreate(
            order_id=order.id,
            method=PaymentMethod.COD,
            amount=Decimal("65000.00"),
        ),
        created_by=uuid4(),
    )

    assert payment.status == PaymentEventStatus.PENDING
    assert captured["payment"]["method"] == PaymentMethod.COD
    assert captured["payment"]["status"] == PaymentEventStatus.PENDING
    assert "updated_status" not in captured
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.anyio
async def test_card_delivery_payment_marks_order_paid(monkeypatch):
    db = FakeDb()
    order = make_order(order_type=OrderType.DELIVERY)
    captured = {}

    async def get_order(db, order_id):
        return order

    async def create_payment_event(db, **kwargs):
        captured["payment"] = kwargs
        return SimpleNamespace(id=uuid4(), **kwargs)

    async def update_order_status(db, order, *, status=None, payment_status=None):
        captured["updated_status"] = payment_status
        order.payment_status = payment_status
        return order

    monkeypatch.setattr(payment_service.order_repo, "get_order", get_order)
    monkeypatch.setattr(
        payment_service.payment_repo,
        "create_payment_event",
        create_payment_event,
    )
    monkeypatch.setattr(
        payment_service.order_repo,
        "update_order_status",
        update_order_status,
    )

    payment = await payment_service.create_payment(
        db,
        PaymentCreate(
            order_id=order.id,
            method=PaymentMethod.CARD,
            amount=Decimal("65000.00"),
        ),
        created_by=uuid4(),
    )

    assert payment.status == PaymentEventStatus.SUCCESS
    assert captured["payment"]["method"] == PaymentMethod.CARD
    assert captured["updated_status"] == OrderPaymentStatus.PAID
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.anyio
async def test_cod_instore_payment_is_rejected(monkeypatch):
    db = FakeDb()
    order = make_order(order_type=OrderType.INSTORE)

    async def get_order(db, order_id):
        return order

    monkeypatch.setattr(payment_service.order_repo, "get_order", get_order)

    with pytest.raises(ServiceError) as error:
        await payment_service.create_payment(
            db,
            PaymentCreate(
                order_id=order.id,
                method=PaymentMethod.COD,
                amount=Decimal("65000.00"),
            ),
            created_by=uuid4(),
        )

    assert error.value.code == "cod_not_allowed_for_instore_order"
    assert error.value.status_code == 409


@pytest.mark.anyio
async def test_cash_delivery_payment_is_rejected(monkeypatch):
    db = FakeDb()
    order = make_order(order_type=OrderType.DELIVERY)

    async def get_order(db, order_id):
        return order

    monkeypatch.setattr(payment_service.order_repo, "get_order", get_order)

    with pytest.raises(ServiceError) as error:
        await payment_service.create_payment(
            db,
            PaymentCreate(
                order_id=order.id,
                method=PaymentMethod.CASH,
                amount=Decimal("65000.00"),
                amount_received=Decimal("70000.00"),
            ),
            created_by=uuid4(),
        )

    assert error.value.code == "cash_not_allowed_for_delivery_order"
    assert error.value.status_code == 409


@pytest.mark.anyio
async def test_stripe_status_poll_syncs_completed_session(monkeypatch):
    db = FakeDb()
    session_id = "cs_test_paid"
    order = SimpleNamespace(
        id=uuid4(),
        status=OrderStatus.IN_PROGRESS,
        payment_status=OrderPaymentStatus.UNPAID,
        completed_at=None,
    )
    payment = SimpleNamespace(
        id=uuid4(),
        order_id=order.id,
        order=order,
        method=PaymentMethod.BANK_TRANSFER,
        status=PaymentEventStatus.PENDING,
        gateway_transaction_id=session_id,
        metadata_={"checkout_url": "https://checkout.stripe.test/session"},
        paid_at=None,
    )
    captured = {}

    async def get_payment_by_gateway_transaction_id(db, lookup_session_id, **kwargs):
        captured.setdefault("lookups", []).append((lookup_session_id, kwargs))
        return payment

    def retrieve_checkout_session(*, session_id, secret_key):
        captured["retrieved"] = (session_id, secret_key)
        return SimpleNamespace(
            id=session_id,
            status="complete",
            payment_status="paid",
        )

    async def handle_completed(db, session):
        captured["completed_session"] = session.id
        payment.status = PaymentEventStatus.SUCCESS
        payment.paid_at = datetime.now(timezone.utc)
        order.payment_status = OrderPaymentStatus.PAID
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.now(timezone.utc)
        return {"processed": True, "payment_id": payment.id}

    monkeypatch.setattr(
        payment_service.payment_repo,
        "get_payment_by_gateway_transaction_id",
        get_payment_by_gateway_transaction_id,
    )
    monkeypatch.setattr(
        payment_service.stripe_gateway,
        "retrieve_checkout_session",
        retrieve_checkout_session,
    )
    monkeypatch.setattr(
        payment_service,
        "_handle_stripe_checkout_completed",
        handle_completed,
    )
    monkeypatch.setattr(
        payment_service,
        "get_settings",
        lambda: SimpleNamespace(stripe_secret_key="sk_test"),
    )

    status = await payment_service.get_stripe_checkout_session_status(db, session_id)

    assert captured["retrieved"] == (session_id, "sk_test")
    assert captured["completed_session"] == session_id
    assert status["payment_status"] == PaymentEventStatus.SUCCESS
    assert status["order_payment_status"] == OrderPaymentStatus.PAID
    assert status["order_status"] == OrderStatus.COMPLETED
    assert db.commits == 1
    assert db.rollbacks == 0
