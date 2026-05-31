from decimal import Decimal
import os
import unittest
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - registers Person 2 tables
from app.core.database import Base
from app.core.integration_contracts import register_audit_writer, register_financial_record_writer
from app.models.ingredient import Ingredient, InventoryMovement
from app.models.order import Order, OrderStatus, OrderType
from app.schemas.inventory import IngredientCreate, InventoryPurchaseCreate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.payment import CashPaymentCreate
from app.schemas.product import ProductCategoryCreate, ProductCreate, ProductRecipeItem
from app.services import inventory_service, order_service, payment_service, product_service
from app.services.errors import DomainError

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
SAFE_TEST_DATABASE = bool(TEST_DATABASE_URL and TEST_DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"))


@unittest.skipUnless(SAFE_TEST_DATABASE, "Set TEST_DATABASE_URL to a PostgreSQL database ending in _test")
class Person2ServiceIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(TEST_DATABASE_URL)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

        self.audit_events = []
        self.financial_records = []

        async def audit_writer(db, actor_user_id, action, entity_type, entity_id, new_value):
            self.audit_events.append((action, entity_type, entity_id))

        async def financial_writer(db, record_type, source_type, source_id, amount, record_date):
            self.financial_records.append((record_type, source_type, source_id, amount))

        register_audit_writer(audit_writer)
        register_financial_record_writer(financial_writer)
        self.actor_id = uuid.uuid4()

    async def asyncTearDown(self):
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def _create_menu(self, stock: Decimal = Decimal("10")):
        async with self.sessions() as db:
            ingredient = await inventory_service.create_ingredient(
                db,
                IngredientCreate(
                    name="Matcha",
                    unit="g",
                    cost_per_unit=Decimal("2"),
                    minimum_threshold=Decimal("1"),
                ),
            )
            await inventory_service.record_purchase(
                db,
                ingredient.id,
                InventoryPurchaseCreate(quantity=stock, cost_per_unit=Decimal("1")),
                self.actor_id,
            )
            category = await product_service.create_category(
                db, ProductCategoryCreate(name="Drink")
            )
            product = await product_service.create_product(
                db,
                ProductCreate(
                    category_id=category.id,
                    name="Matcha Latte",
                    selling_price=Decimal("80"),
                    ingredients=[
                        ProductRecipeItem(
                            ingredient_id=ingredient.id, quantity_per_serving=Decimal("2")
                        )
                    ],
                ),
            )
        return ingredient, product

    async def test_purchase_updates_stock_and_creates_movement(self):
        ingredient, _ = await self._create_menu()
        async with self.sessions() as db:
            persisted = await db.get(Ingredient, ingredient.id)
            movements = list((await db.execute(select(InventoryMovement))).scalars())
        self.assertEqual(persisted.current_stock, Decimal("10.000"))
        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].stock_after, Decimal("10.000"))

    async def test_completion_deducts_stock_and_records_finance(self):
        ingredient, product = await self._create_menu()
        async with self.sessions() as db:
            order = await order_service.create_order(
                db,
                OrderCreate(
                    order_type=OrderType.instore,
                    items=[OrderItemCreate(product_id=product.id, quantity=2)],
                ),
                self.actor_id,
            )
            await order_service.update_status(db, order.id, OrderStatus.in_progress)
            await payment_service.record_cash_payment(
                db, order.id, CashPaymentCreate(amount_received=Decimal("200")), self.actor_id
            )
            completed = await order_service.complete_order(db, order.id, self.actor_id)

        async with self.sessions() as db:
            persisted_ingredient = await db.get(Ingredient, ingredient.id)
            movements = list((await db.execute(select(InventoryMovement))).scalars())
        self.assertEqual(completed.status, OrderStatus.completed)
        self.assertEqual(persisted_ingredient.current_stock, Decimal("6.000"))
        self.assertEqual(len(movements), 2)
        self.assertEqual([record[0] for record in self.financial_records], ["revenue", "material_cost"])

    async def test_insufficient_stock_rolls_back_completion(self):
        ingredient, product = await self._create_menu(stock=Decimal("1"))
        async with self.sessions() as db:
            order = await order_service.create_order(
                db,
                OrderCreate(
                    order_type=OrderType.instore,
                    items=[OrderItemCreate(product_id=product.id, quantity=1)],
                ),
                self.actor_id,
            )
            await order_service.update_status(db, order.id, OrderStatus.in_progress)
            await payment_service.record_cash_payment(
                db, order.id, CashPaymentCreate(amount_received=Decimal("80")), self.actor_id
            )
            with self.assertRaises(DomainError):
                await order_service.complete_order(db, order.id, self.actor_id)

        async with self.sessions() as db:
            persisted_ingredient = await db.get(Ingredient, ingredient.id)
            persisted_order = await db.get(Order, order.id)
            movements = list((await db.execute(select(InventoryMovement))).scalars())
        self.assertEqual(persisted_ingredient.current_stock, Decimal("1.000"))
        self.assertEqual(persisted_order.status, OrderStatus.in_progress)
        self.assertEqual(len(movements), 1)
        self.assertEqual(self.financial_records, [])


if __name__ == "__main__":
    unittest.main()
