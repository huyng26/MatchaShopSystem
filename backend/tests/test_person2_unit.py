from decimal import Decimal
import unittest
import uuid

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

from app.core.integration_contracts import require_roles
from app.models.order import OrderStatus, OrderType
from app.schemas.inventory import IngredientCreate, InventoryPurchaseCreate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.product import ProductRecipeItem, ProductRecipeUpdate
from app.services.errors import DomainError
from app.services.order_service import validate_status_transition


class Person2SchemaTests(unittest.TestCase):
    def test_ingredient_rejects_negative_cost(self):
        with self.assertRaises(ValidationError):
            IngredientCreate(name="Milk", unit="ml", cost_per_unit=Decimal("-1"))

    def test_purchase_rejects_zero_quantity(self):
        with self.assertRaises(ValidationError):
            InventoryPurchaseCreate(quantity=Decimal("0"), cost_per_unit=Decimal("1"))

    def test_recipe_rejects_duplicate_ingredients(self):
        ingredient_id = uuid.uuid4()
        with self.assertRaises(ValidationError):
            ProductRecipeUpdate(
                ingredients=[
                    ProductRecipeItem(
                        ingredient_id=ingredient_id, quantity_per_serving=Decimal("1")
                    ),
                    ProductRecipeItem(
                        ingredient_id=ingredient_id, quantity_per_serving=Decimal("2")
                    ),
                ]
            )

    def test_delivery_order_requires_address(self):
        with self.assertRaises(ValidationError):
            OrderCreate(
                order_type=OrderType.delivery,
                items=[OrderItemCreate(product_id=uuid.uuid4(), quantity=1)],
            )

    def test_order_rejects_duplicate_products(self):
        product_id = uuid.uuid4()
        with self.assertRaises(ValidationError):
            OrderCreate(
                order_type=OrderType.instore,
                items=[
                    OrderItemCreate(product_id=product_id, quantity=1),
                    OrderItemCreate(product_id=product_id, quantity=2),
                ],
            )


class OrderTransitionTests(unittest.TestCase):
    def test_instore_can_enter_progress(self):
        validate_status_transition(OrderType.instore, OrderStatus.pending, OrderStatus.in_progress)

    def test_delivery_can_become_ready(self):
        validate_status_transition(
            OrderType.delivery, OrderStatus.in_progress, OrderStatus.ready_for_delivery
        )

    def test_generic_endpoint_cannot_complete(self):
        with self.assertRaises(DomainError):
            validate_status_transition(
                OrderType.instore, OrderStatus.in_progress, OrderStatus.completed
            )

    def test_delivery_cannot_skip_progress(self):
        with self.assertRaises(DomainError):
            validate_status_transition(
                OrderType.delivery, OrderStatus.pending, OrderStatus.ready_for_delivery
            )


class SharedContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_unregistered_rbac_contract_fails_explicitly(self):
        request = Request({"type": "http", "method": "GET", "path": "/"})
        with self.assertRaises(HTTPException) as raised:
            await require_roles("admin")(request)
        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
