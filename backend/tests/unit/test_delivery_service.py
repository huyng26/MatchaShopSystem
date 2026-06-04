from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.constants import StaffStatus, UserRole, UserStatus
from app.models.delivery import (
    CodReconciliationStatus,
    DeliveryTripOrderStatus,
    DeliveryTripStatus,
)
from app.models.finance import FinancialRecordType
from app.models.order import OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import PaymentEventStatus, PaymentMethod
from app.schemas.delivery import (
    DeliveryCodReconcile,
    DeliveryOrderDelivered,
    DeliveryOrderFailed,
    DeliveryTripCreate,
)
from app.services import delivery_service
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


def make_user(role: UserRole = UserRole.ADMIN, user_id=None):
    return SimpleNamespace(
        id=user_id or uuid4(),
        email="user@matcha.local",
        role=role,
        status=UserStatus.ACTIVE,
    )


def make_staff(user_id, staff_id=None, role: UserRole = UserRole.SHIPPER):
    return SimpleNamespace(
        id=staff_id or uuid4(),
        user_id=user_id,
        role=role,
        status=StaffStatus.ACTIVE,
    )


def make_order(
    *,
    order_id=None,
    order_code="ORD-TEST",
    status: OrderStatus = OrderStatus.READY_FOR_DELIVERY,
    payment_status: OrderPaymentStatus = OrderPaymentStatus.UNPAID,
    total_amount: Decimal = Decimal("65000.00"),
    lat: Decimal = Decimal("10.7780000"),
    lon: Decimal = Decimal("106.7020000"),
):
    return SimpleNamespace(
        id=order_id or uuid4(),
        order_code=order_code,
        order_type=OrderType.DELIVERY,
        status=status,
        payment_status=payment_status,
        total_amount=total_amount,
        delivery_latitude=lat,
        delivery_longitude=lon,
        payments=[],
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_create_trip_auto_orders_stops_and_sums_expected_cod(monkeypatch):
    db = FakeDb()
    current_user = make_user(UserRole.DELIVERY_MANAGER)
    near_order = make_order(
        order_code="ORD-NEAR",
        total_amount=Decimal("65000.00"),
        lat=Decimal("10.7780000"),
        lon=Decimal("106.7020000"),
    )
    far_order = make_order(
        order_code="ORD-FAR",
        total_amount=Decimal("85000.00"),
        lat=Decimal("10.9000000"),
        lon=Decimal("106.9000000"),
    )
    requested_ids = [far_order.id, near_order.id]
    trip = SimpleNamespace(
        id=uuid4(),
        trip_code="TRIP-TEST",
        status=DeliveryTripStatus.PENDING_DISPATCH,
        expected_cod_amount=Decimal("0.00"),
        trip_orders=[],
    )
    captured = {}

    async def get_orders_by_ids_for_update(db, order_ids):
        assert order_ids == requested_ids
        return [near_order, far_order]

    async def order_has_active_assignment(db, order_id):
        return False

    async def reserve_unique_trip_code(db):
        return "TRIP-TEST"

    async def create_trip(db, *, trip_code, expected_cod_amount, created_by):
        captured["trip_code"] = trip_code
        captured["expected_cod_amount"] = expected_cod_amount
        captured["created_by"] = created_by
        trip.expected_cod_amount = expected_cod_amount
        return trip

    async def create_trip_orders(db, *, trip_id, ordered_order_ids):
        captured["ordered_order_ids"] = ordered_order_ids
        trip.trip_orders = [
            SimpleNamespace(order_id=order_id, stop_order=index + 1)
            for index, order_id in enumerate(ordered_order_ids)
        ]
        return trip.trip_orders

    async def get_trip_detail(db, trip_id):
        return trip

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_orders_by_ids_for_update",
        get_orders_by_ids_for_update,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "order_has_active_assignment",
        order_has_active_assignment,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "reserve_unique_trip_code",
        reserve_unique_trip_code,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "create_trip",
        create_trip,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "create_trip_orders",
        create_trip_orders,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_detail",
        get_trip_detail,
    )

    result = await delivery_service.create_trip(
        db,
        DeliveryTripCreate(order_ids=requested_ids, use_auto_route=True),
        current_user=current_user,
    )

    assert result is trip
    assert db.commits == 1
    assert db.rollbacks == 0
    assert captured["trip_code"] == "TRIP-TEST"
    assert captured["created_by"] == current_user.id
    assert captured["expected_cod_amount"] == Decimal("150000.00")
    assert captured["ordered_order_ids"] == [near_order.id, far_order.id]


@pytest.mark.asyncio
async def test_create_trip_rejects_order_not_ready(monkeypatch):
    db = FakeDb()
    order = make_order(status=OrderStatus.PENDING)

    async def get_orders_by_ids_for_update(db, order_ids):
        return [order]

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_orders_by_ids_for_update",
        get_orders_by_ids_for_update,
    )

    with pytest.raises(ServiceError) as error:
        await delivery_service.create_trip(
            db,
            DeliveryTripCreate(order_ids=[order.id], use_auto_route=True),
            current_user=make_user(UserRole.DELIVERY_MANAGER),
        )

    assert error.value.code == "order_not_ready_for_delivery"
    assert error.value.status_code == 409
    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_mark_order_failed_returns_order_to_queue_and_completes_trip(
    monkeypatch,
):
    db = FakeDb()
    shipper_user = make_user(UserRole.SHIPPER)
    shipper = make_staff(shipper_user.id)
    trip = SimpleNamespace(
        id=uuid4(),
        shipper_id=shipper.id,
        status=DeliveryTripStatus.IN_TRANSIT,
        completed_at=None,
        updated_at=None,
    )
    order = make_order(status=OrderStatus.READY_FOR_DELIVERY)
    trip_order = SimpleNamespace(
        id=uuid4(),
        trip_id=trip.id,
        order_id=order.id,
        order=order,
        trip=trip,
        status=DeliveryTripOrderStatus.ASSIGNED,
        failed_at=None,
        failed_reason=None,
        note=None,
        updated_at=None,
    )

    async def get_trip_for_update(db, trip_id):
        return trip

    async def get_staff_profile_by_user_id(db, user_id):
        return shipper

    async def get_trip_order_detail(db, *, trip_id, order_id):
        return trip_order

    async def update_order_status(db, order, *, status=None, payment_status=None):
        if status is not None:
            order.status = status
        if payment_status is not None:
            order.payment_status = payment_status
        return order

    async def list_trip_orders(db, trip_id):
        return [trip_order]

    async def get_trip_detail(db, trip_id):
        return trip

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_for_update",
        get_trip_for_update,
    )
    monkeypatch.setattr(
        delivery_service.staff_repo,
        "get_staff_profile_by_user_id",
        get_staff_profile_by_user_id,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_order_detail",
        get_trip_order_detail,
    )
    monkeypatch.setattr(
        delivery_service.order_repo,
        "update_order_status",
        update_order_status,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "list_trip_orders",
        list_trip_orders,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_detail",
        get_trip_detail,
    )

    result = await delivery_service.mark_order_failed(
        db,
        trip.id,
        order.id,
        DeliveryOrderFailed(
            failed_reason="Customer unreachable",
            note="Call twice, no answer",
        ),
        current_user=shipper_user,
    )

    assert result is trip
    assert trip_order.status == DeliveryTripOrderStatus.FAILED
    assert trip_order.failed_at is not None
    assert trip_order.failed_reason == "Customer unreachable"
    assert trip_order.note == "Call twice, no answer"
    assert order.status == OrderStatus.READY_FOR_DELIVERY
    assert trip.status == DeliveryTripStatus.COMPLETED
    assert trip.completed_at is not None
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_mark_order_delivered_collects_cod_and_completes_order(monkeypatch):
    db = FakeDb()
    shipper_user = make_user(UserRole.SHIPPER)
    shipper = make_staff(shipper_user.id)
    trip = SimpleNamespace(
        id=uuid4(),
        shipper_id=shipper.id,
        status=DeliveryTripStatus.IN_TRANSIT,
        completed_at=None,
        updated_at=None,
    )
    order = make_order(
        status=OrderStatus.READY_FOR_DELIVERY,
        payment_status=OrderPaymentStatus.UNPAID,
        total_amount=Decimal("65000.00"),
    )
    trip_order = SimpleNamespace(
        id=uuid4(),
        trip_id=trip.id,
        order_id=order.id,
        order=order,
        trip=trip,
        status=DeliveryTripOrderStatus.ASSIGNED,
        cod_collected=Decimal("0.00"),
        delivered_at=None,
        note=None,
        updated_at=None,
    )
    captured = {}

    async def get_trip_for_update(db, trip_id):
        return trip

    async def get_staff_profile_by_user_id(db, user_id):
        return shipper

    async def get_trip_order_detail(db, *, trip_id, order_id):
        return trip_order

    async def get_pending_cod_payment_for_order(db, order_id):
        return None

    async def create_payment_event(db, **kwargs):
        captured["payment"] = kwargs
        return SimpleNamespace(id=uuid4(), **kwargs)

    async def update_order_status(db, order, *, status=None, payment_status=None):
        if status is not None:
            order.status = status
        if payment_status is not None:
            order.payment_status = payment_status
        return order

    async def complete_order_without_commit(db, order_id):
        captured["completed_order_id"] = order_id
        order.status = OrderStatus.COMPLETED

    async def list_trip_orders(db, trip_id):
        return [trip_order]

    async def get_trip_detail(db, trip_id):
        return trip

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_for_update",
        get_trip_for_update,
    )
    monkeypatch.setattr(
        delivery_service.staff_repo,
        "get_staff_profile_by_user_id",
        get_staff_profile_by_user_id,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_order_detail",
        get_trip_order_detail,
    )
    monkeypatch.setattr(
        delivery_service.payment_repo,
        "get_pending_cod_payment_for_order",
        get_pending_cod_payment_for_order,
    )
    monkeypatch.setattr(
        delivery_service.payment_repo,
        "create_payment_event",
        create_payment_event,
    )
    monkeypatch.setattr(
        delivery_service.order_repo,
        "update_order_status",
        update_order_status,
    )
    monkeypatch.setattr(
        delivery_service.order_service,
        "complete_order_without_commit",
        complete_order_without_commit,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "list_trip_orders",
        list_trip_orders,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_detail",
        get_trip_detail,
    )

    result = await delivery_service.mark_order_delivered(
        db,
        trip.id,
        order.id,
        DeliveryOrderDelivered(
            cod_collected=Decimal("65000.00"),
            note="Left with customer",
        ),
        current_user=shipper_user,
    )

    assert result is trip
    assert captured["payment"]["method"] == PaymentMethod.COD
    assert captured["payment"]["status"] == PaymentEventStatus.SUCCESS
    assert captured["payment"]["amount"] == Decimal("65000.00")
    assert captured["payment"]["created_by"] == shipper_user.id
    assert captured["completed_order_id"] == order.id
    assert order.payment_status == OrderPaymentStatus.PAID
    assert order.status == OrderStatus.COMPLETED
    assert trip_order.status == DeliveryTripOrderStatus.DELIVERED
    assert trip_order.cod_collected == Decimal("65000.00")
    assert trip_order.note == "Left with customer"
    assert trip.status == DeliveryTripStatus.COMPLETED
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_reconcile_cod_requires_reason_when_amount_differs(monkeypatch):
    db = FakeDb()
    current_user = make_user(UserRole.DELIVERY_MANAGER)
    trip = SimpleNamespace(
        id=uuid4(),
        shipper_id=uuid4(),
        status=DeliveryTripStatus.COMPLETED,
        trip_orders=[
            SimpleNamespace(
                status=DeliveryTripOrderStatus.DELIVERED,
                cod_collected=Decimal("65000.00"),
            )
        ],
    )

    async def get_trip_detail(db, trip_id):
        return trip

    async def get_reconciliation_by_trip(db, trip_id):
        return None

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_detail",
        get_trip_detail,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_reconciliation_by_trip",
        get_reconciliation_by_trip,
    )

    with pytest.raises(ServiceError) as error:
        await delivery_service.reconcile_cod(
            db,
            trip.id,
            DeliveryCodReconcile(actual_amount=Decimal("60000.00")),
            current_user=current_user,
        )

    assert error.value.code == "cod_discrepancy_reason_required"
    assert error.value.status_code == 422
    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_reconcile_cod_confirms_exact_amount(monkeypatch):
    db = FakeDb()
    current_user = make_user(UserRole.DELIVERY_MANAGER)
    trip = SimpleNamespace(
        id=uuid4(),
        shipper_id=uuid4(),
        status=DeliveryTripStatus.COMPLETED,
        trip_orders=[
            SimpleNamespace(
                status=DeliveryTripOrderStatus.DELIVERED,
                cod_collected=Decimal("65000.00"),
            )
        ],
        actual_cod_amount=None,
        discrepancy_amount=None,
        discrepancy_reason=None,
        reconciled_at=None,
        updated_at=None,
    )
    captured = {}

    async def get_trip_detail(db, trip_id):
        return trip

    async def get_reconciliation_by_trip(db, trip_id):
        return None

    async def create_reconciliation(db, **kwargs):
        captured["reconciliation"] = kwargs
        return SimpleNamespace(id=uuid4(), **kwargs)

    async def create_financial_record(db, **kwargs):
        captured["financial_record"] = kwargs

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_detail",
        get_trip_detail,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_reconciliation_by_trip",
        get_reconciliation_by_trip,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "create_reconciliation",
        create_reconciliation,
    )
    monkeypatch.setattr(
        delivery_service.finance_repo,
        "create_financial_record",
        create_financial_record,
    )

    result = await delivery_service.reconcile_cod(
        db,
        trip.id,
        DeliveryCodReconcile(actual_amount=Decimal("65000.00")),
        current_user=current_user,
    )

    assert result.status == CodReconciliationStatus.CONFIRMED
    assert captured["reconciliation"]["expected_amount"] == Decimal("65000.00")
    assert captured["reconciliation"]["actual_amount"] == Decimal("65000.00")
    assert captured["reconciliation"]["discrepancy_amount"] == Decimal("0.00")
    assert captured["reconciliation"]["reconciled_by"] == current_user.id
    assert "financial_record" not in captured
    assert trip.status == DeliveryTripStatus.RECONCILED
    assert trip.actual_cod_amount == Decimal("65000.00")
    assert trip.discrepancy_amount == Decimal("0.00")
    assert db.commits == 1
    assert db.rollbacks == 0
    assert db.refreshes == 1


@pytest.mark.asyncio
async def test_reconcile_cod_flags_discrepancy_and_records_finance(monkeypatch):
    db = FakeDb()
    current_user = make_user(UserRole.DELIVERY_MANAGER)
    trip = SimpleNamespace(
        id=uuid4(),
        shipper_id=uuid4(),
        status=DeliveryTripStatus.COMPLETED,
        trip_orders=[
            SimpleNamespace(
                status=DeliveryTripOrderStatus.DELIVERED,
                cod_collected=Decimal("65000.00"),
            )
        ],
    )
    captured = {}

    async def get_trip_detail(db, trip_id):
        return trip

    async def get_reconciliation_by_trip(db, trip_id):
        return None

    async def create_reconciliation(db, **kwargs):
        reconciliation = SimpleNamespace(id=uuid4(), **kwargs)
        captured["reconciliation"] = reconciliation
        return reconciliation

    async def create_financial_record(db, **kwargs):
        captured["financial_record"] = kwargs

    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_trip_detail",
        get_trip_detail,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "get_reconciliation_by_trip",
        get_reconciliation_by_trip,
    )
    monkeypatch.setattr(
        delivery_service.delivery_repo,
        "create_reconciliation",
        create_reconciliation,
    )
    monkeypatch.setattr(
        delivery_service.finance_repo,
        "create_financial_record",
        create_financial_record,
    )

    result = await delivery_service.reconcile_cod(
        db,
        trip.id,
        DeliveryCodReconcile(
            actual_amount=Decimal("60000.00"),
            discrepancy_reason="Missing cash",
        ),
        current_user=current_user,
    )

    assert result.status == CodReconciliationStatus.FLAGGED_FOR_REVIEW
    assert result.discrepancy_amount == Decimal("-5000.00")
    assert captured["financial_record"]["record_type"] == (
        FinancialRecordType.COD_RECONCILIATION
    )
    assert captured["financial_record"]["source_type"] == "cod_reconciliation"
    assert captured["financial_record"]["amount"] == Decimal("5000.00")
    assert captured["financial_record"]["record_date"] == result.reconciled_at.date()
    assert captured["financial_record"]["locked"] is True
    assert trip.status == DeliveryTripStatus.RECONCILED
    assert db.commits == 1
    assert db.rollbacks == 0
