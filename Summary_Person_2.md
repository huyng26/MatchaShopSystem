# Person 2 Backend Summary

## Scope Implemented

Person 2 owns inventory, products and recipes, orders, payments, and the atomic
order-completion transaction. The early integer-ID scaffold was replaced with
the UUID-based target described in `plan.md`.

## Main Changes

### Database Models and Migration

Added Alembic revision:

```text
backend/alembic/versions/0001_person2_domains.py
```

Added UUID-based models and database constraints for:

```text
product_categories
products
ingredients
product_recipes
orders
order_items
payments
inventory_purchases
inventory_movements
```

The migration enforces non-negative stock, valid prices, positive recipe and
order quantities, and unique recipe ingredients per product.

### Architecture

Person 2 code now follows this flow:

```text
API route -> service -> repository -> SQLAlchemy model
```

Repositories only query or stage database changes. Services own transaction
boundaries and commit once after the full business operation succeeds.

### Inventory

Implemented ingredient CRUD, purchase recording, movement history, and
low-stock lookup.

Purchase recording is atomic:

1. Lock the ingredient row.
2. Insert the purchase.
3. Insert a `purchase` inventory movement.
4. Increase stock.
5. Commit once.

### Products and Recipes

Implemented category CRUD, product CRUD, availability toggle, recipe lookup,
and recipe replacement.

Products cannot be deleted when referenced by order items. Ingredients cannot
be deleted while an active recipe references them.

### Orders

Implemented order creation, list/detail lookup, status changes, cancellation,
and completion.

Order creation reads product prices from the database and stores price
snapshots in `order_items`. Delivery details are stored directly on `orders`.

### Payments

Implemented:

```text
cash
mock card approval or decline
pending bank transfer and verification
pending COD for delivery orders
```

Payments update payment state but do not complete orders automatically.

### Atomic Order Completion

`order_service.complete_order(...)` is reusable by both the order API and the
future Person 3 delivery workflow.

It performs one transaction:

1. Lock the order.
2. Validate status and payment.
3. Aggregate recipe requirements.
4. Lock ingredients.
5. Reject insufficient stock before changing rows.
6. Deduct stock and write inventory movements.
7. Calculate material cost.
8. Mark the order completed.
9. Request revenue and material-cost financial records.
10. Request an audit record.
11. Commit once or roll back everything.

## Shared Contracts Still Required

Person 1 must register:

```python
register_role_checker(...)
register_audit_writer(...)
```

Person 3 must register:

```python
register_financial_record_writer(...)
```

These hooks are defined in:

```text
backend/app/core/integration_contracts.py
```

Until RBAC is registered, protected HTTP endpoints intentionally return:

```text
503 RBAC integration is not registered
```

Until audit and finance writers are registered, operations requiring those
records intentionally roll back instead of silently omitting required data.

## Verification Completed

Completed checks:

```text
Python compilation
SQLAlchemy mapper configuration
Alembic upgrade SQL generation
Alembic downgrade SQL generation
Direct health/status smoke checks
Unit test suite
```

Always-on test result:

```text
10 passed
```

Three PostgreSQL integration tests are also included. They run only when
`TEST_DATABASE_URL` points to a PostgreSQL database whose name ends in `_test`.

## Swagger API Groups

Swagger is available at:

```text
http://localhost:8000/docs
```

Implemented API groups:

```text
Health
Inventory
Products
Orders
Payments
```
