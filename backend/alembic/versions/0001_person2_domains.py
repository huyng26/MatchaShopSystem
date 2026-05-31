"""Create Person 2 domain tables.

Revision ID: 0001_person2_domains
Revises:
Create Date: 2026-05-31

The users and customers foreign keys are added by their owning migrations.
Their UUID contract is represented by created_by and customer_id columns here.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_person2_domains"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps(include_deleted: bool = False) -> list[sa.Column]:
    columns = [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]
    if include_deleted:
        columns.append(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    return columns


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamps(include_deleted=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("current_stock", sa.Numeric(12, 3), nullable=False),
        sa.Column("cost_per_unit", sa.Numeric(12, 2), nullable=False),
        sa.Column("minimum_threshold", sa.Numeric(12, 3), nullable=False),
        *_timestamps(include_deleted=True),
        sa.CheckConstraint("current_stock >= 0", name="ck_ingredients_current_stock_non_negative"),
        sa.CheckConstraint("cost_per_unit >= 0", name="ck_ingredients_cost_per_unit_non_negative"),
        sa.CheckConstraint(
            "minimum_threshold >= 0", name="ck_ingredients_minimum_threshold_non_negative"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_ingredients_name", "ingredients", ["name"])
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("selling_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        *_timestamps(include_deleted=True),
        sa.CheckConstraint("selling_price > 0", name="ck_products_selling_price_positive"),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_table(
        "product_recipes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("ingredient_id", sa.Uuid(), nullable=False),
        sa.Column("quantity_per_serving", sa.Numeric(12, 3), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("quantity_per_serving > 0", name="ck_product_recipes_quantity_positive"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id", "ingredient_id", name="uq_product_recipes_product_ingredient"
        ),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_code", sa.String(50), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("order_type", sa.Enum("instore", "delivery", name="ordertype"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "ready_for_delivery",
                "completed",
                "cancelled",
                name="orderstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.Enum("unpaid", "paid", "refunded", name="orderpaymentstatus"),
            nullable=False,
        ),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("customer_phone", sa.String(20), nullable=True),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("delivery_latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("delivery_longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        *_timestamps(include_deleted=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_orders_discount_non_negative"),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_code"),
    )
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_order_code", "orders", ["order_code"])
    op.create_index("ix_orders_order_type", "orders", ["order_type"])
    op.create_index("ix_orders_payment_status", "orders", ["payment_status"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price > 0", name="ck_order_items_unit_price_positive"),
        sa.CheckConstraint("line_total > 0", name="ck_order_items_line_total_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column(
            "method",
            sa.Enum("cash", "card", "bank_transfer", "cod", name="paymentmethod"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "success", "failed", "cancelled", name="paymentstatus"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_received", sa.Numeric(12, 2), nullable=True),
        sa.Column("change_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("gateway_transaction_id", sa.String(255), nullable=True),
        sa.Column("bank_reference_number", sa.String(255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        sa.CheckConstraint(
            "amount_received IS NULL OR amount_received >= 0",
            name="ck_payments_amount_received_non_negative",
        ),
        sa.CheckConstraint(
            "change_amount IS NULL OR change_amount >= 0",
            name="ck_payments_change_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_method", "payments", ["method"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_table(
        "inventory_purchases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ingredient_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("cost_per_unit", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("supplier_name", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("purchased_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_purchases_quantity_positive"),
        sa.CheckConstraint("cost_per_unit >= 0", name="ck_inventory_purchases_cost_non_negative"),
        sa.CheckConstraint("total_cost >= 0", name="ck_inventory_purchases_total_non_negative"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_purchases_ingredient_id", "inventory_purchases", ["ingredient_id"])
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ingredient_id", sa.Uuid(), nullable=False),
        sa.Column(
            "movement_type",
            sa.Enum(
                "purchase",
                "sale_deduction",
                "cancellation_restore",
                "manual_adjustment",
                "waste",
                name="inventorymovementtype",
            ),
            nullable=False,
        ),
        sa.Column("quantity_change", sa.Numeric(12, 3), nullable=False),
        sa.Column("stock_before", sa.Numeric(12, 3), nullable=False),
        sa.Column("stock_after", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("reference_type", sa.String(100), nullable=True),
        sa.Column("reference_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity_change <> 0", name="ck_inventory_movements_quantity_non_zero"),
        sa.CheckConstraint(
            "stock_before >= 0", name="ck_inventory_movements_stock_before_non_negative"
        ),
        sa.CheckConstraint("stock_after >= 0", name="ck_inventory_movements_stock_after_non_negative"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_movements_created_at", "inventory_movements", ["created_at"])
    op.create_index("ix_inventory_movements_ingredient_id", "inventory_movements", ["ingredient_id"])


def downgrade() -> None:
    op.drop_table("inventory_movements")
    op.drop_table("inventory_purchases")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("product_recipes")
    op.drop_table("products")
    op.drop_table("ingredients")
    op.drop_table("product_categories")
    op.execute("DROP TYPE inventorymovementtype")
    op.execute("DROP TYPE paymentstatus")
    op.execute("DROP TYPE paymentmethod")
    op.execute("DROP TYPE orderpaymentstatus")
    op.execute("DROP TYPE orderstatus")
    op.execute("DROP TYPE ordertype")
