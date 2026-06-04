from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinancialRecordType
from app.models.ingredients import Ingredient
from app.models.inventory import InventoryMovementType
from app.models.order import Order, OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import PaymentMethod
from app.repositories import (
    customer_repo,
    finance_repo,
    inventory_repo,
    order_repo,
    product_repo,
)
from app.schemas.order import (
    OrderCancelResponse,
    OrderCompleteResponse,
    OrderCreate,
    OrderListFilters,
)
from app.services.errors import ServiceError

MONEY_QUANT = Decimal("0.01")


@dataclass(frozen=True)
class PricedOrderItem:
    product_id: UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def create_order(
    db: AsyncSession,
    payload: OrderCreate,
    *,
    created_by: UUID,
) -> Order:
    _validate_delivery_fields(payload)
    if payload.customer_id is not None and not await customer_repo.customer_exists(
        db,
        payload.customer_id,
    ):
        raise ServiceError("customer_not_found", status_code=404)

    priced_items = await _price_order_items(db, payload)
    subtotal = sum((item.line_total for item in priced_items), Decimal("0")).quantize(
        MONEY_QUANT
    )
    if payload.discount_amount > subtotal:
        raise ServiceError("discount_exceeds_subtotal")
    total_amount = (subtotal - payload.discount_amount).quantize(MONEY_QUANT)

    try:
        order_code = await order_repo.reserve_unique_order_code(db)
        order = await order_repo.create_order_header(
            db,
            order_code=order_code,
            order_type=payload.order_type,
            customer_id=payload.customer_id,
            subtotal=subtotal,
            discount_amount=payload.discount_amount,
            total_amount=total_amount,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            delivery_address=payload.delivery_address,
            delivery_latitude=payload.delivery_latitude,
            delivery_longitude=payload.delivery_longitude,
            note=payload.note,
            created_by=created_by,
        )
        await order_repo.create_order_item_rows(
            db,
            order.id,
            [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total,
                }
                for item in priced_items
            ],
        )
        await db.commit()
        detail = await order_repo.get_order_detail(db, order.id)
        if detail is None:
            raise ServiceError("order_not_found", status_code=404)
        return detail
    except Exception:
        await db.rollback()
        raise


async def list_orders(
    db: AsyncSession,
    filters: OrderListFilters | None = None,
) -> Sequence[Order]:
    filters = filters or OrderListFilters()
    return await order_repo.list_orders(
        db,
        status=filters.status,
        payment_status=filters.payment_status,
        order_type=filters.order_type,
        customer_id=filters.customer_id,
        created_from=filters.created_from,
        created_to=filters.created_to,
    )


async def get_order_detail(db: AsyncSession, order_id: UUID) -> Order:
    order = await order_repo.get_order_detail(db, order_id)
    if order is None:
        raise ServiceError("order_not_found", status_code=404)
    return order


async def cancel_order(db: AsyncSession, order_id: UUID) -> OrderCancelResponse:
    order = await get_order_detail(db, order_id)
    if order.status == OrderStatus.COMPLETED:
        raise ServiceError("completed_order_cannot_be_cancelled", status_code=409)
    if order.status == OrderStatus.CANCELLED:
        raise ServiceError("order_already_cancelled", status_code=409)

    try:
        order = await order_repo.set_order_cancelled(db, order)
        await db.commit()
        return OrderCancelResponse.model_validate(order)
    except Exception:
        await db.rollback()
        raise


async def complete_order(db: AsyncSession, order_id: UUID) -> OrderCompleteResponse:
    try:
        order = await order_repo.get_order_detail(db, order_id)
        if order is None:
            raise ServiceError("order_not_found", status_code=404)
        if order.status == OrderStatus.CANCELLED:
            raise ServiceError("cancelled_order_cannot_be_completed", status_code=409)
        if order.status == OrderStatus.COMPLETED:
            raise ServiceError("order_already_completed", status_code=409)
        if not _has_completion_payment(order):
            raise ServiceError("order_payment_required", status_code=409)

        required_quantities = await _calculate_required_ingredient_quantities(db, order)
        locked_ingredients = await inventory_repo.lock_ingredients_by_ids(
            db,
            list(required_quantities),
        )
        ingredients_by_id = {
            ingredient.id: ingredient for ingredient in locked_ingredients
        }

        insufficient = _find_insufficient_stock(required_quantities, ingredients_by_id)
        if insufficient:
            raise ServiceError(
                "insufficient_stock",
                status_code=409,
                context={"ingredients": insufficient},
            )

        material_cost = Decimal("0")
        for ingredient_id, required_quantity in required_quantities.items():
            ingredient = ingredients_by_id[ingredient_id]
            stock_before = ingredient.current_stock
            stock_after = stock_before - required_quantity
            material_cost += required_quantity * ingredient.cost_per_unit

            ingredient.current_stock = stock_after
            await inventory_repo.update_ingredient(db, ingredient)
            await inventory_repo.create_movement(
                db,
                ingredient_id=ingredient.id,
                movement_type=InventoryMovementType.SALE_DEDUCTION,
                quantity_change=-required_quantity,
                stock_before=stock_before,
                stock_after=stock_after,
                unit_cost=ingredient.cost_per_unit,
                reference_type="order",
                reference_id=order.id,
                created_by=order.created_by,
            )

        completed_at = utc_now()
        order = await order_repo.set_order_completed(
            db,
            order,
            completed_at=completed_at,
        )

        await _create_completion_financial_records(
            db,
            order=order,
            material_cost=material_cost.quantize(MONEY_QUANT),
            record_date=completed_at.date(),
        )
        await db.commit()
        return OrderCompleteResponse(
            id=order.id,
            status=order.status,
            inventory_deducted=True,
            financial_records_created=True,
            completed_at=order.completed_at,
        )
    except Exception:
        await db.rollback()
        raise


def _validate_delivery_fields(payload: OrderCreate) -> None:
    if payload.order_type != OrderType.DELIVERY:
        return

    missing = [
        field
        for field in ("customer_name", "customer_phone", "delivery_address")
        if not getattr(payload, field)
    ]
    if missing:
        raise ServiceError(
            "delivery_fields_required",
            context={"fields": missing},
        )


async def _price_order_items(
    db: AsyncSession,
    payload: OrderCreate,
) -> list[PricedOrderItem]:
    priced_items: list[PricedOrderItem] = []

    for item in payload.items:
        product = await product_repo.get_product(db, item.product_id)
        if product is None:
            raise ServiceError("product_not_found", status_code=404)
        if not product.is_available:
            raise ServiceError(
                "product_unavailable",
                status_code=409,
                context={"product_id": str(product.id)},
            )
        if item.quantity <= 0:
            raise ServiceError("order_item_quantity_must_be_positive")

        line_total = (product.selling_price * item.quantity).quantize(MONEY_QUANT)
        priced_items.append(
            PricedOrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.selling_price,
                line_total=line_total,
            )
        )

    return priced_items


def _has_completion_payment(order: Order) -> bool:
    if order.payment_status == OrderPaymentStatus.PAID:
        return True

    return bool(
        order.order_type == OrderType.DELIVERY
        and any(payment.method == PaymentMethod.COD for payment in order.payments)
    )


async def _calculate_required_ingredient_quantities(
    db: AsyncSession,
    order: Order,
) -> dict[UUID, Decimal]:
    required: dict[UUID, Decimal] = {}

    for item in order.items:
        recipe_rows = await product_repo.list_product_recipe_rows(
            db,
            item.product_id,
            load_ingredients=True,
        )
        for recipe_row in recipe_rows:
            quantity = recipe_row.quantity_per_serving * item.quantity
            required[recipe_row.ingredient_id] = (
                required.get(recipe_row.ingredient_id, Decimal("0")) + quantity
            )

    return required


def _find_insufficient_stock(
    required_quantities: dict[UUID, Decimal],
    ingredients_by_id: dict[UUID, Ingredient],
) -> list[dict[str, str]]:
    insufficient: list[dict[str, str]] = []

    for ingredient_id, required_quantity in required_quantities.items():
        ingredient = ingredients_by_id.get(ingredient_id)
        if ingredient is None:
            insufficient.append(
                {
                    "id": str(ingredient_id),
                    "name": "",
                    "required": str(required_quantity),
                    "available": "0",
                }
            )
            continue

        if ingredient.current_stock < required_quantity:
            insufficient.append(
                {
                    "id": str(ingredient.id),
                    "name": ingredient.name,
                    "required": str(required_quantity),
                    "available": str(ingredient.current_stock),
                }
            )

    return insufficient


async def _create_completion_financial_records(
    db: AsyncSession,
    *,
    order: Order,
    material_cost: Decimal,
    record_date: date,
) -> None:
    revenue_exists = await finance_repo.completion_record_exists(
        db,
        source_type="order",
        source_id=order.id,
        record_type=FinancialRecordType.REVENUE,
    )
    if not revenue_exists:
        await finance_repo.create_financial_record(
            db,
            record_type=FinancialRecordType.REVENUE,
            source_type="order",
            source_id=order.id,
            amount=order.total_amount,
            record_date=record_date,
            locked=True,
        )

    material_cost_exists = await finance_repo.completion_record_exists(
        db,
        source_type="order",
        source_id=order.id,
        record_type=FinancialRecordType.MATERIAL_COST,
    )
    if not material_cost_exists:
        await finance_repo.create_financial_record(
            db,
            record_type=FinancialRecordType.MATERIAL_COST,
            source_type="order",
            source_id=order.id,
            amount=material_cost,
            record_date=record_date,
            locked=True,
        )
