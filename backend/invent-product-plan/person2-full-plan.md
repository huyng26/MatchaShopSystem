# Person 2 Full Backend Coding Plan

## Summary

Implement the Product/Inventory/Order/Payment backend work in seven steps:

1. SQLAlchemy models matching `backend/db/init/*.sql`
2. Pydantic schemas based on SQL columns and current mock API response shapes
3. Repositories
4. Services
5. Replace mock API routes with service calls
6. Unit tests
7. Integration tests

Current mock routes in `backend/app/api/v1/` are the frontend compatibility
baseline. The real APIs should keep the same top-level response format from
`app/core/responses.py` and preserve existing fields where they already exist:

- Products return `id`, `category_id`, `name`, `description`, `selling_price`,
  `is_available`.
- Categories return `id`, `name`, `description`.
- Ingredients return `id`, `name`, `unit`, `current_stock`, `cost_per_unit`,
  `minimum_threshold`.
- Orders return order header fields plus `items`.
- Payments return `id`, `order_id`, `method`, `status`, `amount`, `paid_at`.

## Step 1 - SQLAlchemy Models

Code the ORM layer first because schemas, repositories, and services all depend
on consistent model names and relationships.

### Files to code

- `backend/app/models/product.py`
- `backend/app/models/ingredients.py`
- `backend/app/models/inventory.py`
- `backend/app/models/order.py`
- `backend/app/models/payment.py`
- `backend/app/models/finance.py`
- `backend/app/models/user.py` and `backend/app/models/customer.py` only if
  minimal referenced models are still placeholders when implementation begins.
- `backend/app/models/__init__.py`

### Model classes to create

- `ProductCategory` -> `product_categories`
- `Product` -> `products`
- `Ingredient` -> `ingredients`
- `ProductRecipe` -> `product_recipes`
- `InventoryPurchase` -> `inventory_purchases`
- `InventoryMovement` -> `inventory_movements`
- `Order` -> `orders`
- `OrderItem` -> `order_items`
- `Payment` -> `payments`
- `FinancialRecord` -> `financial_records`

### Enums to create

Define Python enum classes using the exact lowercase values from
`backend/db/init/002_types.sql`:

- `OrderType`: `instore`, `delivery`
- `OrderStatus`: `pending`, `in_progress`, `ready_for_delivery`, `completed`,
  `cancelled`
- `OrderPaymentStatus`: `unpaid`, `paid`, `refunded`
- `PaymentMethod`: `cash`, `card`, `bank_transfer`, `cod`
- `PaymentEventStatus`: `pending`, `success`, `failed`, `cancelled`
- `InventoryMovementType`: `purchase`, `sale_deduction`,
  `cancellation_restore`, `manual_adjustment`, `waste`
- `FinancialRecordType`: `revenue`, `material_cost`, `operating_expense`,
  `cod_reconciliation`, `refund`

Use SQLAlchemy `Enum` with `name=` matching the existing PostgreSQL type names.
Do not create new enum type names.

### Column rules

- Use `UUID(as_uuid=True)` for UUID fields.
- Use `Numeric(12, 2)` for money fields.
- Use `Numeric(12, 3)` for stock/recipe quantity fields.
- Use timezone-aware `DateTime(timezone=True)` for `timestamptz`.
- Use `Date` for `financial_records.record_date`.
- Keep SQL defaults aligned with DB defaults where useful, but do not rely on
  ORM defaults to replace DB constraints.
- Include `deleted_at` only on tables that have it in SQL.

### Relationships

Add relationships that support service queries:

- Category has many products.
- Product belongs to category.
- Product has many recipe rows.
- Ingredient has many recipe rows, purchases, and movements.
- Product recipe belongs to product and ingredient.
- Order has many order items and payments.
- Order item belongs to order and product.
- Payment belongs to order.

### Acceptance checks

- `Base.metadata` includes all Person 2 tables.
- Model table names and column names exactly match SQL.
- Relationship names are readable and stable.
- No migration is added unless SQL files are intentionally changed.

## Step 2 - Pydantic Schemas

Code schemas after models so response classes mirror database fields and current
mock route payloads.

### Files to code

- `backend/app/schemas/product.py`
- `backend/app/schemas/inventory.py`
- `backend/app/schemas/order.py`
- `backend/app/schemas/payment.py`
- `backend/app/schemas/finance.py` only for `FinancialRecordRead` if needed by
  tests or completion responses.

### Product schemas

Create:

- `ProductCategoryCreate`
- `ProductCategoryUpdate`
- `ProductCategoryRead`
- `ProductCreate`
- `ProductUpdate`
- `ProductAvailabilityUpdate`
- `ProductRead`
- `RecipeItemCreate`
- `RecipeItemRead`
- `ProductRecipeRead`
- `ProductRecipeUpdate`

Preserve mock product/category response fields:

- `ProductRead`: `id`, `category_id`, `name`, `description`,
  `selling_price`, `is_available`.
- `ProductCategoryRead`: `id`, `name`, `description`.

Add `created_at` and `updated_at` only if the route intentionally exposes them.
For frontend compatibility, do not remove existing mock fields.

### Inventory schemas

Create:

- `IngredientCreate`
- `IngredientUpdate`
- `IngredientRead`
- `InventoryPurchaseCreate`
- `InventoryPurchaseRead`
- `InventoryMovementRead`
- `LowStockIngredientRead`

Preserve mock ingredient response fields:

- `id`, `name`, `unit`, `current_stock`, `cost_per_unit`,
  `minimum_threshold`.

Purchase input should include:

- `quantity`
- `cost_per_unit`
- `supplier_name`
- `notes`
- `purchased_at`

Do not let clients send `total_cost`; services calculate it.

### Order schemas

Create:

- `OrderItemCreate`
- `OrderItemRead`
- `OrderCreate`
- `OrderRead`
- `OrderDetailRead`
- `OrderListFilters`
- `OrderCancelResponse`
- `OrderCompleteResponse`

Preserve mock order fields:

- `id`, `order_code`, `customer_id`, `order_type`, `status`,
  `payment_status`, `subtotal`, `discount_amount`, `total_amount`,
  `created_at`, `items`.

Include delivery fields for delivery orders:

- `customer_name`
- `customer_phone`
- `delivery_address`
- `delivery_latitude`
- `delivery_longitude`
- `note`

`OrderItemRead` should include:

- `product_id`
- `product_name`
- `quantity`
- `unit_price`
- `line_total`

`OrderCreate` should accept product IDs and quantities, not prices.

### Payment schemas

Create:

- `PaymentCreate`
- `PaymentRead`
- `PaymentMethodRead` or return `list[PaymentMethod]`

Preserve mock payment fields:

- `id`, `order_id`, `method`, `status`, `amount`, `paid_at`.

`PaymentCreate` should support:

- `order_id`
- `method`
- `amount`
- `amount_received` for cash
- `gateway_transaction_id` for card
- `bank_reference_number` for bank transfer

### Validation rules

- Product price must be `> 0`.
- Ingredient stock, cost, and threshold must be `>= 0`.
- Recipe quantity must be `> 0`.
- Purchase quantity must be `> 0`.
- Order item quantity must be `> 0`.
- Payment amount must be `> 0`.
- Delivery latitude must be `-90..90`.
- Delivery longitude must be `-180..180`.
- Use `ConfigDict(from_attributes=True)` on read schemas.

## Step 3 - Repositories

Repositories should contain database access only. They should not decide
business rules beyond query filtering and persistence details.

### Files to code

- `backend/app/repositories/product_repo.py`
- `backend/app/repositories/inventory_repo.py`
- `backend/app/repositories/order_repo.py`
- `backend/app/repositories/payment_repo.py`
- `backend/app/repositories/finance_repo.py`

### Product repository functions

Implement helpers for:

- List/get/create/update/soft-delete categories.
- List/get/create/update/soft-delete products.
- Filter products by `is_available`, `category_id`, and non-deleted status.
- Check category exists and is not deleted.
- Check product exists and is not deleted.
- Check product is referenced by `order_items`.
- List product recipe rows.
- Replace product recipe rows in one session transaction.
- Check all recipe ingredient IDs exist and are not deleted.

### Inventory repository functions

Implement helpers for:

- List/get/create/update/soft-delete ingredients.
- Check ingredient is referenced by active product recipes.
- List purchases.
- Create purchase row.
- List movements.
- Create movement row.
- List low-stock ingredients using
  `current_stock <= minimum_threshold`.
- Lock ingredient rows by IDs using `SELECT ... FOR UPDATE` for stock-changing
  flows.

### Order repository functions

Implement helpers for:

- Generate or reserve unique order codes.
- List orders with filters for status, payment status, order type, customer,
  and date range.
- Get order detail with items and products loaded.
- Create order header.
- Create order item rows.
- Update order status/payment status.
- Set `completed_at` and `cancelled_at`.
- Check order is not soft-deleted.

### Payment repository functions

Implement helpers for:

- List payments by optional order ID/method/status.
- Create payment event.
- Get successful payment for order.
- Sum successful payments for an order if multiple are allowed later.

### Finance repository functions

Implement helpers for:

- Create financial record.
- List records by source type/source ID for tests and verification.
- Prevent duplicate completion records if the service retries completion for an
  already completed order.

## Step 4 - Services

Services own validation, business rules, transactions, and repository
orchestration.

### Product service

Code functions for:

- Create/list/get/update/delete categories.
- Create/list/get/update/delete products.
- Toggle product availability.
- Get product recipe.
- Replace product recipe.

Rules:

- Product creation validates category exists.
- Product update cannot set invalid price.
- Product delete soft-deletes when unused.
- Product delete is blocked if product appears in `order_items`; return a clear
  API error such as `product_linked_to_orders`.
- Recipe update validates product exists, all ingredients exist, no duplicate
  ingredient IDs, and every quantity is positive.

### Inventory service

Code functions for:

- Create/list/get/update/delete ingredients.
- Record ingredient purchase.
- List purchases.
- List movements.
- List low-stock ingredients.

Rules:

- Ingredient delete is blocked if used by active product recipes.
- Purchase recording runs in one transaction:
  - load and lock ingredient
  - calculate `total_cost = quantity * cost_per_unit`
  - create `inventory_purchases`
  - create `inventory_movements` with `movement_type = purchase`
  - update `ingredients.current_stock`
  - commit once
- Every stock change must include `stock_before`, `stock_after`, and
  `quantity_change`.

### Order service

Code functions for:

- Create order.
- List orders.
- Get order detail.
- Cancel order.
- Complete order.

Rules:

- Clients send `product_id` and `quantity`; backend reads product prices.
- Reject unavailable or deleted products.
- Calculate `unit_price`, `line_total`, `subtotal`, `discount_amount`, and
  `total_amount` server-side.
- Validate delivery fields when `order_type = delivery`.
- Cancel only orders that are not already completed or cancelled.
- Completion must reject cancelled/completed orders.
- Completion should require `payment_status = paid`, except COD delivery can be
  left as a placeholder rule for Person 3 delivery completion.

### Payment service

Code functions for:

- List payments.
- Create payment.
- List payment methods.

Rules:

- Cash payment requires `amount_received >= order.total_amount`.
- Cash payment calculates `change_amount`.
- Card and bank transfer are mock-success in v1.
- COD creates a pending or placeholder payment without marking non-delivered
  orders completed.
- Successful payment sets `orders.payment_status = paid`.

### Order completion transaction

Implement in `order_service.complete_order`.

Required transaction:

1. Load order detail and validate status/payment.
2. Load all order item products and product recipes.
3. Calculate required ingredient quantities across all items.
4. Lock all ingredient rows with `FOR UPDATE`.
5. If any stock is insufficient, rollback and return an error listing the
   ingredient IDs/names.
6. Deduct each ingredient stock.
7. Insert one `sale_deduction` inventory movement per ingredient.
8. Calculate material cost from deducted quantity and ingredient cost.
9. Mark order `completed` and set `completed_at`.
10. Insert `financial_records`:
    - `revenue`, `source_type = order`, `source_id = order.id`
    - `material_cost`, `source_type = order`, `source_id = order.id`
11. Commit once.

## Step 5 - Replace Mock API Routes

Replace mock data blocks in `backend/app/api/v1/` after services exist.

### Existing mock route compatibility

Keep these existing paths working:

- `GET /api/v1/products`
- `GET /api/v1/products/categories`
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/ingredients`
- `GET /api/v1/ingredients/low-stock`
- `GET /api/v1/orders`
- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/complete`
- `GET /api/v1/payments`
- `POST /api/v1/payments`
- `GET /api/v1/payments/methods`

### Additional real endpoints to add

Products:

- `POST /api/v1/products`
- `PUT /api/v1/products/{product_id}`
- `PATCH /api/v1/products/{product_id}/availability`
- `DELETE /api/v1/products/{product_id}`
- `GET /api/v1/products/{product_id}/recipe`
- `PUT /api/v1/products/{product_id}/recipe`
- `POST /api/v1/products/categories`
- `PUT /api/v1/products/categories/{category_id}`
- `DELETE /api/v1/products/categories/{category_id}`

Ingredients and inventory:

- `GET /api/v1/ingredients/{ingredient_id}`
- `POST /api/v1/ingredients`
- `PUT /api/v1/ingredients/{ingredient_id}`
- `DELETE /api/v1/ingredients/{ingredient_id}`
- `POST /api/v1/ingredients/{ingredient_id}/purchases`
- `GET /api/v1/inventory/purchases`
- `GET /api/v1/inventory/movements`
- `GET /api/v1/inventory/low-stock`

Orders:

- `POST /api/v1/orders/{order_id}/cancel`

### Route coding rules

- Inject `AsyncSession` with `Depends(get_db)`.
- Accept Pydantic request schemas, not raw `dict`.
- Call one service function per endpoint.
- Wrap results in `success_response` or `created_response`.
- Raise `HTTPException` with stable detail codes for known business failures.
- Do not put SQL queries or business logic in route modules.
- Register `app/api/v1/inventory.py` in `router.py` if the separate inventory
  route module is added.

## Step 6 - Unit Tests

Unit tests should validate services and business rules without depending on
HTTP route behavior.

### Files to create

- `backend/tests/unit/test_product_service.py`
- `backend/tests/unit/test_inventory_service.py`
- `backend/tests/unit/test_order_service.py`
- `backend/tests/unit/test_payment_service.py`

### Product unit tests

- Creating product rejects missing category.
- Creating product rejects non-positive price.
- Availability toggle changes only `is_available`.
- Recipe update rejects duplicate ingredient IDs.
- Recipe update rejects zero or negative quantity.
- Product delete is blocked when linked to order items.

### Inventory unit tests

- Ingredient create rejects negative stock/cost/threshold.
- Purchase calculates total cost.
- Purchase increases stock.
- Purchase creates movement with correct before/after stock.
- Low-stock returns only ingredients where stock is at or below threshold.
- Ingredient delete is blocked when used by active recipe.

### Order unit tests

- Order creation copies current product price.
- Order creation calculates line totals and order totals.
- Order creation rejects unavailable products.
- Delivery order validates required delivery fields.
- Cancel rejects completed orders.
- Complete order rejects unpaid orders.
- Complete order rejects insufficient stock and does not mutate stock.
- Complete order deducts stock and creates sale deduction movements.
- Complete order creates revenue and material cost records.

### Payment unit tests

- Cash payment rejects insufficient `amount_received`.
- Cash payment calculates change.
- Successful payment marks order paid.
- Card and bank transfer produce mock successful payments.
- COD does not accidentally complete the order.

## Step 7 - Integration Tests

Integration tests should verify route wiring, response shape, and DB persistence.

### Files to create

- `backend/tests/integration/test_product_api.py`
- `backend/tests/integration/test_inventory_api.py`
- `backend/tests/integration/test_order_payment_completion_api.py`

### Test setup

- Use an isolated test database or transaction rollback fixture.
- Apply SQL init schema before tests, or create metadata tables only if the
  project standardizes on ORM-created test tables.
- Override `get_db` so API tests use the test session.
- Seed a minimal `users` row because purchases, orders, and payments require
  `created_by`.

### Product API scenarios

- Create category.
- List categories and verify mock-compatible fields.
- Create product.
- List products and verify mock-compatible fields.
- Get product detail.
- Toggle availability.
- Update product.
- Create/update recipe.
- Delete unused product.
- Block deleting product linked to an order.

### Inventory API scenarios

- Create ingredient.
- List ingredients and verify mock-compatible fields.
- Get ingredient detail.
- Record purchase.
- Verify stock increased.
- Verify purchase appears in `/inventory/purchases`.
- Verify movement appears in `/inventory/movements`.
- Verify low-stock endpoint behavior.
- Block deleting ingredient used by recipe.

### Order/payment/completion API scenarios

- Create category, ingredient, purchase, product, and recipe.
- Create order using product ID and quantity.
- Verify order totals are backend-calculated.
- Record successful cash payment.
- Verify order payment status becomes `paid`.
- Complete order.
- Verify order status becomes `completed`.
- Verify ingredient stock decreased.
- Verify `sale_deduction` movement exists.
- Verify revenue and material-cost financial records exist.

### Failure API scenarios

- Product creation with invalid category returns a business error.
- Recipe update with missing ingredient returns a business error.
- Order creation with unavailable product returns a business error.
- Payment with insufficient cash received returns a business error.
- Complete order with insufficient stock returns a business error and leaves
  stock unchanged.

## Implementation Order

Use this order when coding:

1. Models and enums.
2. Schemas.
3. Product repository/service/routes/tests.
4. Inventory repository/service/routes/tests.
5. Order repository/service/routes/tests.
6. Payment repository/service/routes/tests.
7. Completion transaction and finance record tests.
8. Full integration flow.

## Assumptions

- The SQL files in `backend/db/init/` remain the schema source of truth.
- Existing mock route response fields are frontend compatibility requirements.
- Auth/RBAC dependencies can be added later by Person 1; this plan keeps route
  structure ready for dependency injection.
- Person 2 creates `financial_records` during completion, but Person 3 owns
  finance reporting APIs.
- COD delivery finalization will be completed later with Person 3 delivery work.
