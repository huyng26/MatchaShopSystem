from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.order import OrderPaymentStatus, OrderStatus, OrderType
from app.schemas.order import OrderCreate
from app.services import order_service
from app.services.errors import ServiceError


class FakeDb:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.refreshes = 0

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def flush(self) -> None:
        self.flushes += 1

    async def refresh(self, obj) -> None:
        self.refreshes += 1
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()


def make_payload(**overrides) -> OrderCreate:
    data = {
        "order_type": OrderType.INSTORE,
        "customer_phone": "0912345678",
        "items": [{"product_id": uuid4(), "quantity": 2}],
    }
    data.update(overrides)
    return OrderCreate(**data)


def make_product(product_id, price=Decimal("30000.00")):
    return SimpleNamespace(
        id=product_id,
        selling_price=price,
        is_available=True,
    )


async def setup_create_order_repos(monkeypatch, *, detail_order=None):
    captured = {}

    async def get_product(db, product_id):
        return make_product(product_id)

    async def reserve_unique_order_code(db):
        return "ORD-TEST"

    async def create_order_header(db, **kwargs):
        captured["order"] = kwargs
        return SimpleNamespace(
            id=uuid4(),
            status=OrderStatus.PENDING,
            payment_status=OrderPaymentStatus.UNPAID,
            items=[],
            payments=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            completed_at=None,
            cancelled_at=None,
            **kwargs,
        )

    async def create_order_item_rows(db, order_id, items):
        captured["items"] = list(items)
        return []

    async def get_order_detail(db, order_id):
        if detail_order is not None:
            return detail_order
        return SimpleNamespace(
            id=order_id,
            items=[],
            payments=[],
            **captured["order"],
        )

    monkeypatch.setattr(order_service.product_repo, "get_product", get_product)
    monkeypatch.setattr(
        order_service.order_repo,
        "reserve_unique_order_code",
        reserve_unique_order_code,
    )
    monkeypatch.setattr(
        order_service.order_repo,
        "create_order_header",
        create_order_header,
    )
    monkeypatch.setattr(
        order_service.order_repo,
        "create_order_item_rows",
        create_order_item_rows,
    )
    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)
    return captured


@pytest.mark.asyncio
async def test_instore_order_links_existing_customer_by_phone(monkeypatch):
    db = FakeDb()
    customer = SimpleNamespace(
        id=uuid4(),
        name="Nguyen An",
        phone="0912345678",
    )

    async def get_customer_by_phone(db, phone):
        return customer

    monkeypatch.setattr(
        order_service.customer_repo,
        "get_customer_by_phone",
        get_customer_by_phone,
    )
    captured = await setup_create_order_repos(monkeypatch)

    result = await order_service.create_order(
        db,
        make_payload(),
        created_by=uuid4(),
    )

    assert result.customer_id == customer.id
    assert captured["order"]["customer_id"] == customer.id
    assert captured["order"]["customer_name"] == "Nguyen An"
    assert captured["order"]["customer_phone"] == "0912345678"
    assert captured["order"]["total_amount"] == Decimal("60000.00")
    assert db.added == []
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_instore_order_stays_anonymous_when_customer_declines_profile(
    monkeypatch,
):
    db = FakeDb()

    async def get_customer_by_phone(db, phone):
        return None

    monkeypatch.setattr(
        order_service.customer_repo,
        "get_customer_by_phone",
        get_customer_by_phone,
    )
    captured = await setup_create_order_repos(monkeypatch)

    result = await order_service.create_order(
        db,
        make_payload(customer_name="Nguyen An", create_customer_profile=False),
        created_by=uuid4(),
    )

    assert result.customer_id is None
    assert captured["order"]["customer_id"] is None
    assert captured["order"]["customer_name"] is None
    assert captured["order"]["customer_phone"] is None
    assert db.added == []
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_instore_order_creates_customer_profile_when_requested(monkeypatch):
    db = FakeDb()

    async def get_customer_by_phone(db, phone):
        return None

    monkeypatch.setattr(
        order_service.customer_repo,
        "get_customer_by_phone",
        get_customer_by_phone,
    )
    captured = await setup_create_order_repos(monkeypatch)

    result = await order_service.create_order(
        db,
        make_payload(customer_name="Nguyen An", create_customer_profile=True),
        created_by=uuid4(),
    )

    assert len(db.added) == 1
    assert db.added[0].name == "Nguyen An"
    assert db.added[0].phone == "0912345678"
    assert result.customer_id == db.added[0].id
    assert captured["order"]["customer_id"] == db.added[0].id
    assert captured["order"]["customer_name"] == "Nguyen An"
    assert captured["order"]["customer_phone"] == "0912345678"
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_delivery_order_requires_coordinates_before_insert(monkeypatch):
    db = FakeDb()

    with pytest.raises(ServiceError) as error:
        await order_service.create_order(
            db,
            make_payload(
                order_type=OrderType.DELIVERY,
                customer_name="Nguyen An",
                customer_phone="0912345678",
                delivery_address="Quan 3, TP.HCM",
                delivery_latitude=None,
                delivery_longitude=None,
            ),
            created_by=uuid4(),
        )

    assert error.value.code == "delivery_fields_required"
    assert error.value.status_code == 422
    assert db.commits == 0
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_complete_order_adds_loyalty_points_for_linked_customer(monkeypatch):
    db = FakeDb()
    customer_id = uuid4()
    order = SimpleNamespace(
        id=uuid4(),
        order_code="ORD-LOYALTY",
        customer_id=customer_id,
        order_type=OrderType.INSTORE,
        status=OrderStatus.IN_PROGRESS,
        payment_status=OrderPaymentStatus.PAID,
        total_amount=Decimal("65000.00"),
        created_by=uuid4(),
        completed_at=None,
        items=[],
        payments=[],
    )
    captured = {}

    async def get_order_detail(db, order_id):
        return order

    async def lock_ingredients_by_ids(db, ingredient_ids):
        return []

    async def set_order_completed(db, order, *, completed_at=None):
        order.status = OrderStatus.COMPLETED
        order.completed_at = completed_at
        return order

    async def create_completion_financial_records(
        db,
        *,
        order,
        material_cost,
        record_date,
    ):
        captured["material_cost"] = material_cost

    async def add_loyalty_points(db, linked_customer_id, points):
        captured["loyalty"] = (linked_customer_id, points)
        return SimpleNamespace(id=linked_customer_id, loyalty_points=points)

    monkeypatch.setattr(order_service.order_repo, "get_order_detail", get_order_detail)
    monkeypatch.setattr(
        order_service.inventory_repo,
        "lock_ingredients_by_ids",
        lock_ingredients_by_ids,
    )
    monkeypatch.setattr(
        order_service.order_repo,
        "set_order_completed",
        set_order_completed,
    )
    monkeypatch.setattr(
        order_service,
        "_create_completion_financial_records",
        create_completion_financial_records,
    )
    monkeypatch.setattr(
        order_service.customer_repo,
        "add_loyalty_points",
        add_loyalty_points,
    )

    result = await order_service.complete_order(db, order.id)

    assert result.status == OrderStatus.COMPLETED
    assert captured["material_cost"] == Decimal("0.00")
    assert captured["loyalty"] == (customer_id, 6)
    assert db.commits == 1
    assert db.rollbacks == 0
