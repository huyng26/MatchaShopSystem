# Person 2 Backend Implementation Plan

## Summary

Implement inventory, products and recipes, orders, payments, and the atomic
order-completion transaction from `plan.md`. Treat `plan.md` as the canonical
target. Backward compatibility with the early integer-ID scaffold is not
required.

## Shared Contracts

Person 2 integrates with, but does not implement:

- Person 1: UUID base model, `User`, RBAC dependency, audit logger, and standard
  response helpers.
- Person 3: `FinancialRecord` model and repository writer for `revenue` and
  `material_cost` entries.

Until those branches land, keep the required integration points explicit. Do
not silently skip permission checks, audit records, or financial records.

## Person 2 Scope

1. Replace the Person 2 models with UUID-based tables:
   `product_categories`, `products`, `ingredients`, `product_recipes`,
   `orders`, `order_items`, `payments`, `inventory_purchases`, and
   `inventory_movements`.
2. Add repositories with query-only persistence helpers. Repositories must not
   commit.
3. Add transaction-owning services for inventory, products, orders, payments,
   and order completion.
4. Add thin route modules for ingredients, products, orders, and payments.
5. Add a migration for the Person 2-owned tables and indexes.
6. Add focused tests for validation, transition rules, and transaction-critical
   behavior.

## Critical Completion Transaction

`POST /api/v1/orders/{order_id}/complete` and the Person 3 delivery workflow
must call the same service method. In one transaction:

1. Lock the order and validate its status and payment state.
2. Aggregate recipe requirements for all order items.
3. Lock ingredients with `SELECT ... FOR UPDATE`.
4. Reject missing recipes or insufficient stock before changing rows.
5. Deduct stock and insert `sale_deduction` inventory movements.
6. Calculate consumed material cost.
7. Mark the order completed.
8. Insert Person 3 `revenue` and `material_cost` financial records.
9. Insert the Person 1 audit record.
10. Commit once. Roll back every change on any failure.

## Assumptions

- This is a pre-production replacement. No legacy compatibility routes or data
  migration are required.
- Ingredient purchase cost does not overwrite ingredient master cost in v1.
- Person 3 confirms COD collection before invoking order completion.
- Existing local edits in `backend/app/schemas/customer.py` remain untouched.
