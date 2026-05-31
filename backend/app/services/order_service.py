from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.integration_contracts import write_audit, write_financial_record
from app.models.ingredient import InventoryMovement, InventoryMovementType
from app.models.order import Order, OrderItem, OrderPaymentStatus, OrderStatus, OrderType
from app.repositories import inventory as inventory_repo
from app.repositories import order as order_repo
from app.repositories import product as product_repo
from app.schemas.order import OrderCreate
from app.services.errors import DomainError


STATUS_TRANSITIONS: dict[OrderType, dict[OrderStatus, frozenset[OrderStatus]]] = {
    OrderType.instore: {
        OrderStatus.pending: frozenset({OrderStatus.in_progress}),
        OrderStatus.in_progress: frozenset(),
    },
    OrderType.delivery: {
        OrderStatus.pending: frozenset({OrderStatus.in_progress}),
        OrderStatus.in_progress: frozenset({OrderStatus.ready_for_delivery}),
        OrderStatus.ready_for_delivery: frozenset(),
    },
}


def validate_status_transition(order_type: OrderType, current: OrderStatus, target: OrderStatus) -> None:
    if target in {OrderStatus.completed, OrderStatus.cancelled}:
        raise DomainError("Use the dedicated complete or cancel endpoint")
    if target not in STATUS_TRANSITIONS.get(order_type, {}).get(current, frozenset()):
        raise DomainError(f"Invalid order status transition: {current.value} -> {target.value}")


def _completion_status_allowed(order: Order) -> bool:
    if order.order_type == OrderType.instore:
        return order.status == OrderStatus.in_progress
    return order.status == OrderStatus.ready_for_delivery


def _new_order_code() -> str:
    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ORD-{date_prefix}-{uuid.uuid4().hex[:10].upper()}"


async def list_orders(
    db: AsyncSession, skip: int = 0, limit: int = 100, status: OrderStatus | None = None
) -> list[Order]:
    return await order_repo.list_orders(db, skip, limit, status)


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Order:
    order = await order_repo.get_order(db, order_id)
    if order is None:
        raise DomainError("Order not found", 404)
    return order


async def create_order(db: AsyncSession, data: OrderCreate, actor_user_id: uuid.UUID) -> Order:
    async with db.begin():
        product_ids = {item.product_id for item in data.items}
        products = {product.id: product for product in await product_repo.get_products(db, product_ids)}
        missing = product_ids - products.keys()
        if missing:
            raise DomainError(f"Products not found: {sorted(str(item) for item in missing)}", 404)
        unavailable = [product.name for product in products.values() if not product.is_available]
        if unavailable:
            raise DomainError(f"Products are unavailable: {sorted(unavailable)}")

        order = Order(
            order_code=_new_order_code(),
            customer_id=data.customer_id,
            order_type=data.order_type,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            delivery_address=data.delivery_address,
            delivery_latitude=data.delivery_latitude,
            delivery_longitude=data.delivery_longitude,
            note=data.note,
            created_by=actor_user_id,
        )
        db.add(order)
        await db.flush()

        subtotal = Decimal("0")
        for item_data in data.items:
            unit_price = Decimal(products[item_data.product_id].selling_price)
            line_total = unit_price * item_data.quantity
            subtotal += line_total
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )
        order.subtotal = subtotal
        order.discount_amount = Decimal("0")
        order.total_amount = subtotal
        await db.flush()
        await db.refresh(order, attribute_names=["items"])
    return order


async def update_status(
    db: AsyncSession, order_id: uuid.UUID, target: OrderStatus
) -> Order:
    async with db.begin():
        order = await order_repo.get_order_for_update(db, order_id)
        if order is None:
            raise DomainError("Order not found", 404)
        validate_status_transition(order.order_type, order.status, target)
        order.status = target
    return order


async def cancel_order(db: AsyncSession, order_id: uuid.UUID, actor_user_id: uuid.UUID) -> Order:
    async with db.begin():
        order = await order_repo.get_order_for_update(db, order_id)
        if order is None:
            raise DomainError("Order not found", 404)
        if order.status in {OrderStatus.completed, OrderStatus.cancelled}:
            raise DomainError("Completed or cancelled orders cannot be cancelled")
        order.status = OrderStatus.cancelled
        order.cancelled_at = datetime.now(timezone.utc)
        await write_audit(db, actor_user_id, "order.cancelled", "order", order.id)
    return order


async def complete_order(db: AsyncSession, order_id: uuid.UUID, actor_user_id: uuid.UUID) -> Order:
    async with db.begin():
        order = await order_repo.get_order_for_update(db, order_id)
        if order is None:
            raise DomainError("Order not found", 404)
        if order.status == OrderStatus.completed:
            raise DomainError("Order is already completed")
        if not _completion_status_allowed(order):
            raise DomainError("Order status does not allow completion")
        if order.payment_status != OrderPaymentStatus.paid:
            raise DomainError("Order must be paid before completion")

        product_ids = {item.product_id for item in order.items}
        recipes = await product_repo.list_recipes_for_products(db, product_ids)
        recipes_by_product = defaultdict(list)
        for recipe in recipes:
            recipes_by_product[recipe.product_id].append(recipe)
        missing_recipes = product_ids - recipes_by_product.keys()
        if missing_recipes:
            raise DomainError(
                f"Products have no recipe: {sorted(str(item) for item in missing_recipes)}"
            )

        required_by_ingredient: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0"))
        for item in order.items:
            for recipe in recipes_by_product[item.product_id]:
                required_by_ingredient[recipe.ingredient_id] += (
                    Decimal(recipe.quantity_per_serving) * item.quantity
                )

        ingredients = {
            ingredient.id: ingredient
            for ingredient in await inventory_repo.get_ingredients_for_update(
                db, required_by_ingredient.keys()
            )
        }
        missing_ingredients = required_by_ingredient.keys() - ingredients.keys()
        if missing_ingredients:
            raise DomainError(
                f"Ingredients not found: {sorted(str(item) for item in missing_ingredients)}"
            )

        insufficient: list[str] = []
        for ingredient_id, required in required_by_ingredient.items():
            ingredient = ingredients[ingredient_id]
            if Decimal(ingredient.current_stock) < required:
                insufficient.append(
                    f"{ingredient.name}: required {required}, available {ingredient.current_stock}"
                )
        if insufficient:
            raise DomainError(f"Insufficient stock: {sorted(insufficient)}")

        material_cost = Decimal("0")
        for ingredient_id, required in required_by_ingredient.items():
            ingredient = ingredients[ingredient_id]
            stock_before = Decimal(ingredient.current_stock)
            stock_after = stock_before - required
            ingredient.current_stock = stock_after
            material_cost += required * Decimal(ingredient.cost_per_unit)
            db.add(
                InventoryMovement(
                    ingredient_id=ingredient.id,
                    movement_type=InventoryMovementType.sale_deduction,
                    quantity_change=-required,
                    stock_before=stock_before,
                    stock_after=stock_after,
                    unit_cost=ingredient.cost_per_unit,
                    reference_type="order",
                    reference_id=order.id,
                    created_by=actor_user_id,
                )
            )

        now = datetime.now(timezone.utc)
        order.status = OrderStatus.completed
        order.completed_at = now
        await write_financial_record(
            db, "revenue", "order", order.id, Decimal(order.total_amount), now.date()
        )
        await write_financial_record(db, "material_cost", "order", order.id, material_cost, now.date())
        await write_audit(db, actor_user_id, "order.completed", "order", order.id)
    return order
