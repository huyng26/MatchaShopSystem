# Backend Build Plan — Matcha Shop Business Management System

## 0. Purpose of This Plan

This document is the step-by-step backend implementation plan for the Matcha Shop Business Management System. It is written for a 3-person backend team and focuses on building a clean, consistent, maintainable FastAPI + PostgreSQL backend from scratch.

The system must support these core business areas:

- Authentication and role-based access control
- Account and staff management
- POS order creation and payment processing
- Product/menu management
- Ingredient inventory and recipe/BOM management
- Automatic inventory deduction when orders are completed
- Financial recording and reporting
- Customer management
- Delivery queue, batching, shipper assignment, routing, delivery status, and COD reconciliation
- Dashboard/reporting APIs

The most important backend principle is this:

> Build the OLTP system first. Keep the database normalized and transaction-safe. Add OLAP/reporting through views, summary queries, or materialized views later if needed.

---

## 1. Backend Architecture Decision

### 1.1 Recommended Architecture

Use a **modular monolith**.

Do not split into microservices. The system is still small enough to keep in one backend codebase, but the code must be organized by domain modules.

Recommended backend stack:

```text
Language: Python
Framework: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy 2.0
Migration: Alembic
Validation: Pydantic v2
Authentication: JWT access token + refresh token
Password hashing: bcrypt
Testing: Pytest
Containerization: Docker + Docker Compose
API style: REST JSON API
Optional real-time: WebSocket or Server-Sent Events for delivery tracking
```

### 1.2 Backend Principles

All team members must follow these principles:

1. API routes must stay thin.
2. Business logic must live in service classes/functions.
3. Database access must go through repository functions when queries become complex.
4. Every write operation that changes multiple tables must use a database transaction.
5. The frontend must never be trusted for price, stock, role, or permission decisions.
6. Backend must calculate order totals, payment validity, stock deduction, and financial records.
7. Use soft delete for important business records instead of physical deletion.
8. Use consistent response format for all APIs.
9. Every protected endpoint must check the current user role.
10. Every important business event must be auditable.

---

## 2. Unified Code Structure

All backend developers must use this exact project structure unless the team agrees to change it.

```text
matcha-backend/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── accounts.py
│   │       ├── staff.py
│   │       ├── customers.py
│   │       ├── products.py
│   │       ├── ingredients.py
│   │       ├── orders.py
│   │       ├── payments.py
│   │       ├── deliveries.py
│   │       ├── shipper.py
│   │       ├── finance.py
│   │       └── dashboard.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── exceptions.py
│   │   ├── responses.py
│   │   └── constants.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── staff.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── payment.py
│   │   ├── delivery.py
│   │   ├── shipper.py
│   │   ├── finance.py
│   │   └── audit.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── account.py
│   │   ├── staff.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── payment.py
│   │   ├── delivery.py
│   │   ├── finance.py
│   │   └── common.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── account_service.py
│   │   ├── staff_service.py
│   │   ├── customer_service.py
│   │   ├── product_service.py
│   │   ├── inventory_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   ├── delivery_service.py
│   │   ├── shipper_service.py
│   │   ├── routing_service.py
│   │   ├── finance_service.py
│   │   └── dashboard_service.py
│   │
│   ├── repositories/
│   │   ├── user_repo.py
│   │   ├── staff_repo.py
│   │   ├── customer_repo.py
│   │   ├── product_repo.py
│   │   ├── inventory_repo.py
│   │   ├── order_repo.py
│   │   ├── payment_repo.py
│   │   ├── delivery_repo.py
│   │   └── finance_repo.py
│   │
│   ├── utils/
│   │   ├── pagination.py
│   │   ├── datetime.py
│   │   ├── money.py
│   │   ├── id_generator.py
│   │   └── distance.py
│   │
│   └── seed/
│       └── seed_data.py
│
├── alembic/
├── tests/
│   ├── unit/
│   └── integration/
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── alembic.ini
├── .env.example
└── README.md
```

### 2.1 Naming Rules

Use the same naming style everywhere.

```text
Python files: snake_case.py
Python classes: PascalCase
Python functions: snake_case
Database tables: plural snake_case
Database columns: snake_case
Enum values: lowercase snake_case
API routes: kebab-case or plural noun paths
```

Examples:

```text
products
order_items
inventory_movements
payment_status
ready_for_delivery
```

### 2.2 API Route Rules

Use `/api/v1` prefix for all APIs.

Examples:

```http
POST   /api/v1/auth/login
GET    /api/v1/products
POST   /api/v1/orders
POST   /api/v1/orders/{order_id}/complete
POST   /api/v1/maps/geocode
GET    /api/v1/deliveries/queue
POST   /api/v1/deliveries/trips/{trip_id}/assign
```

### 2.3 Response Format

All APIs must return a consistent structure.

Success:

```json
{
  "success": true,
  "message": "Product created successfully",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Invalid request",
  "errors": [
    {
      "field": "quantity",
      "message": "Quantity must be greater than 0"
    }
  ]
}
```

Pagination:

```json
{
  "success": true,
  "message": "Fetched successfully",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 3. Database Modeling Strategy

### 3.1 OLTP First, OLAP Later

The system has both OLTP and OLAP needs.

OLTP examples:

- Create order
- Record payment
- Deduct inventory
- Assign shipper
- Mark delivery as delivered
- Record expense

OLAP/reporting examples:

- Today revenue
- Monthly profit
- Best-selling products
- Inventory consumption
- Delivery performance

For version 1, use **one PostgreSQL database** with normalized OLTP tables. Reporting APIs can query these tables directly. If reports become slow, add SQL views or materialized views later.

Do not create a separate data warehouse in version 1.

### 3.2 Fact and Dimension Thinking

Do not necessarily name tables `fact_` and `dim_` in the operational database, but understand the meaning:

Dimensions are descriptive/master data:

- users
- staff_profiles
- customers
- products
- product_categories
- ingredients

Facts are business events/transactions:

- orders
- order_items
- payments
- inventory_movements
- inventory_purchases
- expenses
- financial_records
- delivery_trips
- delivery_trip_orders
- cod_reconciliations

Bridge/mapping table:

- product_recipes

---

## 4. Final Database Model for Version 1

This model avoids unnecessary tables while still supporting the required workflows.

### 4.1 Common Columns

Most tables should have:

```text
id UUID primary key
created_at timestamptz not null
updated_at timestamptz not null
deleted_at timestamptz nullable
```

Use `deleted_at` for soft delete where business records should not be physically removed immediately.

### 4.2 Users

Purpose: login account and role-based access.

```text
users
- id UUID PK
- email varchar unique not null
- hashed_password varchar not null
- role enum not null
- status enum not null default 'active'
- last_login_at timestamptz nullable
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Allowed roles:

```text
admin
inventory_manager
delivery_manager
cashier
shipper
```

Allowed user status:

```text
active
inactive
locked
```

Account records are login credentials for RBAC and audit trails. Staff-specific
accounts should normally be created from the staff profile flow so the account
can be linked immediately.

### 4.3 Staff Profiles

Purpose: employee information. A user account may have one staff profile, but a
staff profile does not always need a login account.

```text
staff_profiles
- id UUID PK
- user_id UUID FK users.id unique nullable
- full_name varchar not null
- phone varchar unique not null
- email varchar unique not null
- role enum not null
- salary numeric(12,2) nullable
- date_joined date not null
- status enum not null default 'active'
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```


Do not create a separate employee account table. `users` handles login, `staff_profiles` handles staff details.
When a staff member needs system access, create or link one matching `users`
account through `staff_profiles.user_id`. The user role and staff role must
match. Shipper staff must always be linked to a shipper account because delivery
trips, location updates, and COD actions are assigned to individual shippers.

### 4.4 Staff Tasks

Purpose: task assignment and tracking.

```text
staff_tasks
- id UUID PK
- staff_id UUID FK staff_profiles.id not null
- title varchar not null
- description text nullable
- due_date date not null
- priority enum not null
- status enum not null default 'pending'
- created_by UUID FK users.id not null
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Allowed task status:

```text
pending
in_progress
done
```

### 4.5 Customers

Purpose: customer profile and purchase history.

```text
customers
- id UUID PK
- name varchar not null
- phone varchar nullable
- address text nullable
- note text nullable
- loyalty_points integer not null default 0
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Do not create a separate loyalty table in version 1. Keep `loyalty_points` in `customers` unless the project later needs detailed loyalty transaction history.

### 4.6 Product Categories

Purpose: group products.

```text
product_categories
- id UUID PK
- name varchar unique not null
- description text nullable
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

### 4.7 Products

Purpose: menu items sold through POS or delivery.

```text
products
- id UUID PK
- category_id UUID FK product_categories.id not null
- name varchar not null
- description text nullable
- selling_price numeric(12,2) not null
- is_available boolean not null default true
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Important rules:

- Product price must be greater than 0.
- Product cannot be deleted if it appears in existing order items.
- If a product is no longer sold, set `is_available = false` instead of deleting.

### 4.8 Ingredients

Purpose: ingredient master data and current stock.

```text
ingredients
- id UUID PK
- name varchar unique not null
- unit varchar not null
- current_stock numeric(12,3) not null default 0
- cost_per_unit numeric(12,2) not null
- minimum_threshold numeric(12,3) not null default 0
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Important rules:

- `current_stock` must never be negative.
- `cost_per_unit` must be greater than or equal to 0.
- Ingredient cannot be deleted if used in an active product recipe.

### 4.9 Product Recipes

Purpose: BOM/recipe mapping between product and ingredients.

```text
product_recipes
- id UUID PK
- product_id UUID FK products.id not null
- ingredient_id UUID FK ingredients.id not null
- quantity_per_serving numeric(12,3) not null
- created_at timestamptz
- updated_at timestamptz
```

Constraints:

```text
unique(product_id, ingredient_id)
quantity_per_serving > 0
```

This is not a dimension or fact table. It is a bridge table.

Example:

```text
Product: Matcha Latte
- Matcha powder: 10 g
- Milk: 200 ml
- Cup: 1 piece
```

### 4.10 Orders

Purpose: order header for in-store and delivery orders.

```text
orders
- id UUID PK
- order_code varchar unique not null
- customer_id UUID FK customers.id nullable
- order_type enum not null
- status enum not null default 'pending'
- payment_status enum not null default 'unpaid'
- subtotal numeric(12,2) not null default 0
- discount_amount numeric(12,2) not null default 0
- total_amount numeric(12,2) not null default 0
- customer_name varchar nullable
- customer_phone varchar nullable
- delivery_address text nullable
- delivery_latitude numeric(10,7) nullable
- delivery_longitude numeric(10,7) nullable
- delivery_formatted_address text nullable
- delivery_place_id varchar nullable
- geocoded_at timestamptz nullable
- geocoding_status varchar nullable
- map_provider varchar nullable
- note text nullable
- created_by UUID FK users.id not null
- created_at timestamptz
- updated_at timestamptz
- completed_at timestamptz nullable
- cancelled_at timestamptz nullable
- deleted_at timestamptz nullable
```

Allowed order type:

```text
instore
delivery
```

Allowed order status:

```text
pending
in_progress
ready_for_delivery
completed
cancelled
```

Allowed payment status:

```text
unpaid
paid
refunded
```

Why keep delivery fields in `orders` instead of creating `order_delivery_info`?

Because delivery requirements are not complex enough to justify another table in version 1. The delivery-specific fields are only needed for delivery orders and can stay nullable.

Delivery coordinate rule:

```text
Delivery orders require recipient name, phone, and delivery_address.
delivery_latitude and delivery_longitude are optional request fields.
If both coordinates are provided, backend treats them as a map-confirmed pin and uses them as the delivery location.
If coordinates are not provided, backend geocodes delivery_address through the configured map provider.
If only one coordinate is provided, reject the request.
```

### 4.11 Order Items

Purpose: products sold inside an order.

```text
order_items
- id UUID PK
- order_id UUID FK orders.id not null
- product_id UUID FK products.id not null
- quantity integer not null
- unit_price numeric(12,2) not null
- line_total numeric(12,2) not null
- created_at timestamptz
- updated_at timestamptz
```

Important rules:

- `quantity > 0`
- Backend must copy product price into `unit_price` at order creation time.
- Do not calculate totals based on current product price later, because product prices can change.

### 4.12 Payments

Purpose: payment event for an order.

```text
payments
- id UUID PK
- order_id UUID FK orders.id not null
- method enum not null
- status enum not null default 'pending'
- amount numeric(12,2) not null
- amount_received numeric(12,2) nullable
- change_amount numeric(12,2) nullable
- gateway_transaction_id varchar nullable
- bank_reference_number varchar nullable
- paid_at timestamptz nullable
- created_by UUID FK users.id not null
- created_at timestamptz
- updated_at timestamptz
```

Allowed method:

```text
cash
card
bank_transfer
cod
```

Allowed status:

```text
pending
success
failed
cancelled
```

Version 1 can assume one successful payment per order. Later, if split payment is needed, this table already supports multiple payments per order.

### 4.13 Inventory Purchases

Purpose: record ingredient purchases.

```text
inventory_purchases
- id UUID PK
- ingredient_id UUID FK ingredients.id not null
- quantity numeric(12,3) not null
- cost_per_unit numeric(12,2) not null
- total_cost numeric(12,2) not null
- supplier_name varchar nullable
- notes text nullable
- purchased_at timestamptz not null
- created_by UUID FK users.id not null
- created_at timestamptz
- updated_at timestamptz
```

Important rules:

- `quantity > 0`
- `cost_per_unit >= 0`
- `total_cost = quantity * cost_per_unit`
- Recording a purchase must also create an inventory movement and update ingredient stock in the same transaction.

### 4.14 Inventory Movements

Purpose: inventory ledger. This is necessary because current stock alone does not explain why stock changed.

```text
inventory_movements
- id UUID PK
- ingredient_id UUID FK ingredients.id not null
- movement_type enum not null
- quantity_change numeric(12,3) not null
- stock_before numeric(12,3) not null
- stock_after numeric(12,3) not null
- unit_cost numeric(12,2) nullable
- reference_type varchar nullable
- reference_id UUID nullable
- created_by UUID FK users.id nullable
- created_at timestamptz
```

Allowed movement types:

```text
purchase
sale_deduction
cancellation_restore
manual_adjustment
waste
```

Why this table is necessary:

- Purchase increases stock.
- Completed order decreases stock.
- Cancelled order may restore stock.
- Manual correction changes stock.
- Waste/expired ingredients decrease stock.

Do not remove this table. It is critical for audit and reporting.

### 4.15 Expenses

Purpose: manual operating expense entries.

```text
expenses
- id UUID PK
- category varchar not null
- description text not null
- amount numeric(12,2) not null
- expense_month date not null
- invoice_photo_url text nullable
- created_by UUID FK users.id not null
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Important rules:

- `amount > 0`
- When an expense is recorded, create a financial record in the same transaction.

### 4.16 Financial Records

Purpose: financial ledger for reporting.

```text
financial_records
- id UUID PK
- record_type enum not null
- source_type varchar not null
- source_id UUID not null
- amount numeric(12,2) not null
- record_date date not null
- locked boolean not null default false
- created_at timestamptz
```

Allowed record type:

```text
revenue
material_cost
operating_expense
cod_reconciliation
refund
```

Rules:

- Completed paid order creates `revenue` record.
- Completed order also creates `material_cost` record based on ingredient cost consumed.
- Manual expense creates `operating_expense` record.
- COD reconciliation can create `cod_reconciliation` record if needed.

Why this table is useful:

It makes dashboard and financial reports simple and consistent. Instead of calculating from many tables every time, the finance dashboard can query one ledger table.

### 4.17 Delivery Trips

Purpose: group delivery orders into trips and assign shippers.

```text
delivery_trips
- id UUID PK
- trip_code varchar unique not null
- shipper_id UUID FK staff_profiles.id nullable
- status enum not null default 'pending_dispatch'
- expected_cod_amount numeric(12,2) not null default 0
- actual_cod_amount numeric(12,2) nullable
- discrepancy_amount numeric(12,2) nullable
- discrepancy_reason text nullable
- total_distance_km numeric(10,3) nullable
- total_duration_minutes integer nullable
- route_provider varchar nullable
- started_at timestamptz nullable
- completed_at timestamptz nullable
- reconciled_at timestamptz nullable
- created_by UUID FK users.id not null
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz nullable
```

Allowed trip status:

```text
pending_dispatch
assigned
in_transit
completed
reconciled
cancelled
```

### 4.18 Delivery Trip Orders

Purpose: link orders to a delivery trip.

```text
delivery_trip_orders
- id UUID PK
- trip_id UUID FK delivery_trips.id not null
- order_id UUID FK orders.id not null
- stop_order integer not null
- status enum not null default 'assigned'
- cod_collected numeric(12,2) not null default 0
- distance_from_previous_km numeric(10,3) nullable
- duration_from_previous_minutes integer nullable
- delivered_at timestamptz nullable
- failed_at timestamptz nullable
- failed_reason text nullable
- note text nullable
- created_at timestamptz
- updated_at timestamptz
```

Allowed delivery order status:

```text
assigned
delivered
failed
```

Constraints:

```text
unique(trip_id, order_id)
unique(trip_id, stop_order)
```

### 4.19 Delivery Location Logs

Purpose: GPS location history for active trips.

```text
delivery_location_logs
- id UUID PK
- trip_id UUID FK delivery_trips.id not null
- shipper_id UUID FK staff_profiles.id not null
- latitude numeric(10,7) not null
- longitude numeric(10,7) not null
- recorded_at timestamptz not null
```

Keep this table simple. It is an event log. Route snapshot fields belong on
`delivery_trips` and `delivery_trip_orders`. Query the latest location by
`trip_id` ordered by `recorded_at desc`.

Location source rule:

```text
The backend does not determine the shipper's GPS position by itself.
The shipper client gets latitude/longitude from the device location service
and sends those coordinates to the backend while the trip is in transit.
```

### 4.20 COD Reconciliations

Purpose: close shipper COD cash after delivery.

```text
cod_reconciliations
- id UUID PK
- trip_id UUID FK delivery_trips.id not null unique
- shipper_id UUID FK staff_profiles.id not null
- expected_amount numeric(12,2) not null
- actual_amount numeric(12,2) not null
- discrepancy_amount numeric(12,2) not null
- discrepancy_reason text nullable
- status enum not null default 'confirmed'
- reconciled_by UUID FK users.id not null
- reconciled_at timestamptz not null
```

Allowed status:

```text
confirmed
flagged_for_review
```

### 4.21 Audit Logs

Purpose: record critical operations.

```text
audit_logs
- id UUID PK
- actor_user_id UUID FK users.id nullable
- action varchar not null
- entity_type varchar not null
- entity_id UUID nullable
- old_value jsonb nullable
- new_value jsonb nullable
- ip_address varchar nullable
- created_at timestamptz
```

Log these actions:

- Login success/failure
- Account created/updated/deleted
- Product deleted/hidden
- Ingredient stock adjustment
- Payment success/failure
- Order completed/cancelled
- COD reconciliation discrepancy

---

## 5. Relationship Summary

```text
users 1 --- 0/1 staff_profiles
staff_profiles 1 --- many staff_tasks
customers 1 --- many orders
product_categories 1 --- many products
products 1 --- many order_items
products 1 --- many product_recipes
ingredients 1 --- many product_recipes
ingredients 1 --- many inventory_purchases
ingredients 1 --- many inventory_movements
orders 1 --- many order_items
orders 1 --- many payments
orders many --- many delivery_trips through delivery_trip_orders
delivery_trips 1 --- many delivery_trip_orders
delivery_trips 1 --- many delivery_location_logs
delivery_trips 1 --- 0/1 cod_reconciliations
expenses 1 --- 1 financial_records
orders 1 --- many financial_records
```

---

## 6. Indexing Plan

Add indexes for common filtering and joins.

```text
users.email
staff_profiles.email
staff_profiles.phone
customers.phone
products.name
products.category_id
ingredients.name
orders.order_code
orders.customer_id
orders.status
orders.payment_status
orders.order_type
orders.created_at
order_items.order_id
order_items.product_id
payments.order_id
payments.method
payments.status
inventory_movements.ingredient_id
inventory_movements.created_at
inventory_purchases.ingredient_id
expenses.expense_month
financial_records.record_type
financial_records.record_date
delivery_trips.shipper_id
delivery_trips.status
delivery_trip_orders.trip_id
delivery_trip_orders.order_id
delivery_location_logs.trip_id
delivery_location_logs.recorded_at
```

---

## 7. Backend Build Phases

## Phase 0 — Project Setup

### Goal

Create a runnable backend foundation with database connection, migration, and common utilities.

### Tasks

1. Create FastAPI project.
2. Add Docker Compose with PostgreSQL.
3. Add SQLAlchemy 2.0.
4. Add Alembic migration.
5. Add environment configuration.
6. Add base model class.
7. Add global exception handling.
8. Add standard response helper.
9. Add health check endpoint.
10. Add code formatter and linting.

### Required endpoints

```http
GET /health
GET /api/v1/status
```

### Done when

- Backend starts locally.
- PostgreSQL starts with Docker Compose.
- Alembic can run migration.
- Swagger docs are available.

---

## Phase 1 — Database Migration

### Goal

Implement all required database tables with correct constraints and relationships.

### Tasks

1. Create enum types.
2. Create all SQLAlchemy models.
3. Create initial Alembic migration.
4. Add indexes.
5. Add seed data script.
6. Review ERD with full team before coding business flows.

### Seed Data

Create:

```text
Admin user
Cashier user
Inventory manager user
Delivery manager user
Shipper user

Ingredients:
- Matcha powder
- Fresh milk
- Sugar syrup
- Cup 500ml
- Straw
- Ice

Products:
- Matcha Latte
- Iced Matcha
- Matcha Milk Tea

Customers:
- 3 demo customers
```

### Done when

- All migrations run successfully.
- Seed script creates usable demo data.
- Team agrees table structure matches the business flow.

---

## Phase 2 — Authentication and RBAC

### Goal

Implement secure login and role-based authorization.

### Endpoints

```http
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
```

### Tasks

1. Implement password hashing with bcrypt.
2. Implement JWT access token.
3. Implement refresh token.
4. Implement current user dependency.
5. Implement role permission dependency.
6. Add login audit logging.
7. Add generic login error message.

### Permission helper example

```python
def require_roles(*roles: str):
    ...
```

Usage:

```python
@router.post("/products")
def create_product(
    current_user: User = Depends(require_roles("admin", "inventory_manager"))
):
    ...
```

### Done when

- Users can log in.
- Protected endpoints reject unauthenticated users.
- Admin-only endpoints reject non-admin users.

---

## Phase 3 — Account and Staff Management

### Goal

Allow admin to manage accounts, staff profiles, and staff tasks.

### Account Endpoints

```http
GET    /api/v1/accounts
GET    /api/v1/accounts/{account_id}
POST   /api/v1/accounts
PUT    /api/v1/accounts/{account_id}
DELETE /api/v1/accounts/{account_id}
```

### Staff Endpoints

```http
GET    /api/v1/staff
GET    /api/v1/staff/{staff_id}
POST   /api/v1/staff
PUT    /api/v1/staff/{staff_id}
DELETE /api/v1/staff/{staff_id}
POST   /api/v1/staff/{staff_id}/tasks
PATCH  /api/v1/staff/tasks/{task_id}/status
DELETE /api/v1/staff/tasks/{task_id}
```

### Tasks

1. Account CRUD.
2. Staff profile CRUD, including optional linked account creation.
3. Staff search by name or role.
4. Task assignment.
5. Task status update.
6. Require shipper staff to have a linked shipper account.
7. Prevent deleting staff with active tasks or active delivery/order links.
8. Suggest setting staff inactive instead of deleting.

### Done when

- Admin can create accounts.
- Admin can create and update staff, with or without a linked login account.
- Admin can create shipper staff only when a shipper account is linked or created.
- Admin can assign and update tasks.

---

## Phase 4 — Inventory Management

### Goal

Manage ingredients, stock purchases, stock movement ledger, and low-stock alerts.

### Endpoints

```http
GET    /api/v1/ingredients
GET    /api/v1/ingredients/{ingredient_id}
POST   /api/v1/ingredients
PUT    /api/v1/ingredients/{ingredient_id}
DELETE /api/v1/ingredients/{ingredient_id}
POST   /api/v1/ingredients/{ingredient_id}/purchases
GET    /api/v1/inventory/purchases
GET    /api/v1/inventory/movements
GET    /api/v1/inventory/low-stock
```

### Critical Flow: Record Purchase

When recording a purchase, do this in one transaction:

```text
1. Validate ingredient exists.
2. Validate quantity > 0.
3. Validate cost_per_unit >= 0.
4. Read ingredient current_stock.
5. Insert inventory_purchases row.
6. Insert inventory_movements row:
   - movement_type = purchase
   - quantity_change = positive quantity
   - stock_before = old stock
   - stock_after = old stock + quantity
7. Update ingredients.current_stock.
8. Commit.
```

If any step fails, rollback.

### Done when

- Ingredient CRUD works.
- Purchase recording increases stock.
- Inventory movement is created for every stock change.
- Low-stock endpoint returns ingredients at or below threshold.

---

## Phase 5 — Product/Menu and Recipe/BOM

### Goal

Manage product catalog and connect products to ingredients through recipes.

### Endpoints

```http
GET    /api/v1/categories
POST   /api/v1/categories
PUT    /api/v1/categories/{category_id}
DELETE /api/v1/categories/{category_id}

GET    /api/v1/products
GET    /api/v1/products/{product_id}
POST   /api/v1/products
PUT    /api/v1/products/{product_id}
PATCH  /api/v1/products/{product_id}/availability
DELETE /api/v1/products/{product_id}
GET    /api/v1/products/{product_id}/recipe
PUT    /api/v1/products/{product_id}/recipe
```

### Product Creation Flow

```text
1. Validate category exists.
2. Validate name is not empty.
3. Validate selling_price > 0.
4. If recipe is provided:
   - Validate each ingredient exists.
   - Validate quantity_per_serving > 0.
5. Insert product.
6. Insert recipe rows.
7. Commit.
```

### Product Recipe Update Flow

When updating a recipe:

```text
1. Validate product exists.
2. Validate all ingredients exist.
3. Validate all quantities > 0.
4. Delete old recipe rows for product.
5. Insert new recipe rows.
6. Commit.
```

### Product Delete Rule

```text
If product is used in order_items:
    block deletion
    return message: "Product is linked to existing orders. Hide product instead."
Else:
    soft delete product
```

### Done when

- Product catalog works.
- Product availability toggle affects POS product list.
- Recipes can be created and updated.
- Product deletion is blocked when linked to existing orders.

---

## Phase 6 — Order Management

### Goal

Allow cashier/admin to create and manage orders.

Dependency:

```text
Customer lookup/create/update should be available before order creation. In-store orders may stay anonymous, but the POS checkout should offer customer lookup/creation for loyalty points before the order is saved. Delivery orders must resolve customer/contact/address information before the order is inserted.
```

### Endpoints

```http
GET    /api/v1/orders
GET    /api/v1/orders/{order_id}
POST   /api/v1/orders
POST   /api/v1/maps/geocode
POST   /api/v1/orders/{order_id}/start-processing
POST   /api/v1/orders/{order_id}/ready-for-delivery
POST   /api/v1/orders/{order_id}/cancel
POST   /api/v1/orders/{order_id}/complete
```

### Create Order Flow

```text
1. Cashier builds a POS cart/order draft first.
2. Validate order_type is instore or delivery.
3. Validate at least one item exists.
4. Resolve customer information according to order_type:
   - In-store order:
     - Ask for customer phone at checkout, after the cart is built and before saving the order.
     - If phone matches an existing active customer, link order.customer_id to that customer.
     - Copy customer name/phone into the order snapshot.
     - Use the linked customer_id later for loyalty points and purchase history.
     - If phone does not match any customer, ask whether the customer wants to create a loyalty profile.
     - If yes, collect minimum customer information, create the customer, then link the order.
     - If no, save the order as anonymous with customer_id = null and skip loyalty points.
   - Delivery order:
     - Require recipient name, phone, and delivery address before inserting the order.
     - If delivery_latitude and delivery_longitude are both provided, treat them as a map-confirmed pin and use them as the delivery coordinates.
     - If coordinates are not provided, geocode delivery_address through the configured map provider before inserting the order.
     - If only one coordinate is provided, reject the order as incomplete delivery coordinates.
     - If geocoding fails or returns an ambiguous address, reject the order and ask the client to correct the address or pick a pin on the map.
     - If customer_id is provided, load customer and use it as the linked profile.
     - If customer_id is not provided, find customer by phone.
     - If no customer exists by phone, create the customer in the same transaction.
     - Copy customer/contact/address into order snapshot fields.
5. For each item:
   - Validate product exists.
   - Validate product is available.
   - Validate quantity > 0.
   - Read product selling_price from database.
   - Calculate line_total = selling_price * quantity.
6. Calculate subtotal.
7. Apply discount if supported.
8. Calculate total_amount.
9. Insert order using resolved customer_id and order-time customer/delivery snapshot.
10. Insert order_items.
11. Commit.
```

Do not trust price or total from frontend.

Important rule:

```text
In-store customer linking is optional and exists mainly for loyalty/history. Delivery customer/contact information is required before inserting the order. The order should store both the customer_id link when available and an order-time snapshot, because customer profiles can change after the order is placed.
```

### In-Store Customer/Loyalty Flow

```text
1. Cashier creates the cart.
2. At checkout, cashier asks for customer phone.
3. If customer exists:
   - Link order.customer_id.
   - Copy customer name/phone into order snapshot.
   - Customer can earn loyalty points after the order is completed.
4. If customer does not exist:
   - Ask whether the customer wants to create a loyalty profile.
   - If yes, collect name and phone, create customer, then link order.customer_id.
   - If no, continue anonymous checkout with customer_id = null.
5. Save order.
6. Take payment.
7. Complete order.
8. If order.customer_id is present, add loyalty points and keep order in customer history.
```

### Recommended End-to-End Order Lifecycle

```text
1. Cashier selects order_type.
2. Cashier builds cart.
3. Cashier resolves customer:
   - optional loyalty lookup/create for in-store
   - required for delivery
4. Backend validates products and calculates prices/totals.
5. Backend creates order in pending status.
6. Staff starts preparation:
   pending -> in_progress
7. Payment and fulfillment branch by order_type:
   - In-store:
     - receive cash/card/bank_transfer payment
     - mark payment success and order.payment_status = paid
     - complete order after handoff
     - deduct inventory and create finance records
   - Delivery prepaid:
     - receive card/bank_transfer payment before dispatch
     - mark payment success and order.payment_status = paid
     - mark ready_for_delivery
     - delivery manager batches order into trip
     - shipper marks delivered
     - complete order, deduct inventory, and create finance records
   - Delivery COD:
     - create pending COD payment before ready_for_delivery
     - mark ready_for_delivery
     - delivery manager batches order into trip
     - shipper collects COD and marks delivered
     - mark COD payment success and order.payment_status = paid
     - complete order, deduct inventory, and create finance records in the same delivery transaction
8. If delivery fails:
   - mark delivery_trip_order = failed
   - return order to ready_for_delivery
   - keep COD unpaid/pending
   - do not complete order or deduct inventory yet
9. When trip stops are final:
   - complete trip
   - reconcile COD with delivery manager
```

### Order Status Transition Rules

Allowed transitions:

```text
pending -> in_progress
pending -> ready_for_delivery
pending -> cancelled
in_progress -> ready_for_delivery
in_progress -> completed
in_progress -> cancelled
ready_for_delivery -> completed
ready_for_delivery -> cancelled
completed -> no transition
cancelled -> no transition
```

For delivery orders:

```text
pending -> in_progress -> ready_for_delivery -> completed
pending -> ready_for_delivery is also allowed if ready conditions are satisfied.
```

For in-store orders:

```text
pending -> in_progress -> completed
```

Ready-for-delivery conditions:

```text
- order_type = delivery
- order is not cancelled or completed
- delivery customer/address are present
- delivery coordinates are present, either from map pin or successful backend geocoding
- order is not already assigned to an active delivery trip
- prepaid orders must have successful card or bank_transfer payment
- unpaid orders must have COD pending, or request payment_method = cod to create it
```

### Cancel Order Flow

```text
1. Validate order exists.
2. Validate order is not completed or already cancelled.
3. If inventory was already deducted, restore stock using inventory_movements.
4. Update order status to cancelled.
5. Create audit log.
6. Commit.
```

In version 1, inventory should only be deducted at completion, so cancellation before completion usually does not need restoration.

### Done when

- Orders can be created.
- Order total is calculated by backend.
- Invalid status transitions are blocked.
- Orders can be cancelled according to rules.

---

## Phase 7 — Payment Management

### Goal

Support cash, card, bank transfer, and COD payment records.

### Endpoints

```http
GET  /api/v1/payments
POST /api/v1/payments
GET  /api/v1/payments/methods
```

Current implementation uses one generic `POST /api/v1/payments` endpoint with `method`.

### Cash Payment Flow

```text
1. Validate order exists.
2. Validate order is not cancelled/completed.
3. Validate amount_received >= order.total_amount.
4. Calculate change_amount = amount_received - total_amount.
5. Insert payment with method = cash, status = success.
6. Update order.payment_status = paid.
7. Create audit log.
8. Commit.
```

### Card Payment Flow — Version 1

Because real card gateway integration may not be available, create an interface and mock implementation.

```text
1. Validate order.
2. Call CardPaymentGateway.authorize().
3. If approved:
   - Save gateway_transaction_id.
   - Insert payment success.
   - Mark order paid.
4. If declined:
   - Insert payment failed or return error.
```

### Bank Transfer Flow — Version 1

Use mock bank verification first.

```text
1. Generate payment reference using order_code.
2. Frontend displays QR/bank info.
3. Backend mock endpoint verifies transfer.
4. If amount matches order total:
   - Save bank_reference_number.
   - Insert payment success.
   - Mark order paid.
5. If amount mismatch:
   - Return amount mismatch error.
```

### COD Flow

For delivery orders with COD:

```text
1. Create payment with method = cod, status = pending.
2. Do not mark payment paid immediately.
3. COD is collected when shipper marks delivery as delivered.
4. Payment becomes success after successful delivery/COD collection.
```

Payment method rules:

```text
- In-store orders allow cash, card, bank_transfer.
- Delivery orders allow cod, card, bank_transfer.
- cash is not allowed for delivery.
- cod is not allowed for in-store.
- COD stays pending until shipper marks the order delivered.
```

### Done when

- Cash payment works completely.
- Card and bank transfer are mockable.
- Payment records are linked to orders.
- Order payment status updates correctly.

---

## Phase 8 — Complete Order, Deduct Inventory, Record Finance

### Goal

Implement the most important backend transaction in the system.

### Endpoint

```http
POST /api/v1/orders/{order_id}/complete
```

### Complete Order Flow

This must be atomic.

```text
1. Start database transaction.
2. Load order with order_items.
3. Validate order exists.
4. Validate order status allows completion.
5. Validate payment:
   - In-store order must be paid.
   - Delivery COD order may complete after delivery/COD collection.
6. For each order item:
   - Load product recipe.
   - For each recipe ingredient:
      required_quantity = quantity_per_serving * order_item.quantity
7. Aggregate required quantities by ingredient.
8. Check all ingredient stocks are enough.
9. If any ingredient stock is insufficient:
   - rollback
   - return error listing insufficient ingredients.
10. For each ingredient:
   - stock_before = current_stock
   - stock_after = current_stock - required_quantity
   - update ingredient.current_stock
   - insert inventory_movements row with movement_type = sale_deduction
11. Calculate material cost:
   - material_cost += required_quantity * ingredient.cost_per_unit
12. Update order.status = completed.
13. Set order.completed_at.
14. Insert financial_records revenue row.
15. Insert financial_records material_cost row.
16. If order.customer_id is present:
   - add loyalty_points according to the configured loyalty rule.
   - keep the order visible in customer purchase history.
17. Insert audit log.
18. Commit transaction.
```

### Important Notes

- If stock deduction fails, order must not be completed.
- If finance record creation fails, inventory must not be deducted.
- Loyalty points must only be added after a successful completed paid order.
- If order completion fails, everything must rollback.
- Use row locking when reading ingredients to prevent race conditions.

Example SQLAlchemy idea:

```python
select(Ingredient).where(Ingredient.id.in_(ingredient_ids)).with_for_update()
```

### Done when

- Completing an order deducts inventory.
- Inventory movement rows are created.
- Financial records are created.
- Failed deduction rolls back the whole operation.

---

## Phase 9 — Customer Management

### Goal

Manage customers and show purchase history.

### Endpoints

```http
GET    /api/v1/customers
GET    /api/v1/customers/{customer_id}
POST   /api/v1/customers
PUT    /api/v1/customers/{customer_id}
DELETE /api/v1/customers/{customer_id}
GET    /api/v1/customers/{customer_id}/orders
```

### Tasks

1. Customer CRUD.
2. Phone validation.
3. Customer order history.
4. Soft delete customer.
5. Prevent deleting customer if deletion would break order history. Prefer soft delete.

### Done when

- Customers can be managed.
- Customer order history works.

---

## Phase 10 — Delivery Management

### Goal

Implement delivery queue, batching, route ordering, assignment, delivery status updates, and COD reconciliation.

This is the most challenging part after order completion.

### 10.1 Delivery Concepts

Delivery flow:

```text
1. Delivery order is created with recipient/contact/address information.
2. Backend resolves delivery coordinates:
   - use client-provided lat/lon when the user picked a map pin.
   - otherwise geocode delivery_address through the configured map provider.
3. Order is prepared and marked ready_for_delivery.
4. Delivery manager views delivery queue.
5. Delivery manager requests suggested batches.
6. Backend groups orders by nearby location plus waiting time.
7. Backend optimizes each batch with exact TSP, max 12 stops per trip.
8. Delivery manager creates a trip from a suggested batch or selected order IDs.
9. Backend stores route snapshot on the trip and trip stops.
10. Delivery manager assigns shipper.
11. Shipper starts trip.
12. Shipper client asks the device for GPS permission and reads current location.
13. Shipper client sends location updates to backend while the trip is in_transit.
14. Backend writes location updates to delivery_location_logs.
15. Delivery manager polls trip detail to see latest shipper location.
16. Shipper marks each order delivered or failed.
17. COD is collected if needed.
18. Trip is completed when all stops are final.
19. Delivery manager reconciles COD.
```

### 10.2 Delivery Endpoints

Manager/admin side:

```http
POST /api/v1/maps/geocode
GET  /api/v1/deliveries/queue
POST /api/v1/deliveries/batch/suggest
POST /api/v1/deliveries/trips
GET  /api/v1/deliveries/trips
GET  /api/v1/deliveries/trips/{trip_id}
POST /api/v1/deliveries/trips/{trip_id}/assign
POST /api/v1/deliveries/trips/{trip_id}/reconcile
```

Shipper side:

```http
GET  /api/v1/shipper/trips
GET  /api/v1/shipper/trips/{trip_id}
POST /api/v1/shipper/trips/{trip_id}/start
POST /api/v1/shipper/trips/{trip_id}/location
POST /api/v1/shipper/trips/{trip_id}/orders/{order_id}/delivered
POST /api/v1/shipper/trips/{trip_id}/orders/{order_id}/failed
```

### 10.3 Delivery Queue

Queue should return orders where:

```text
order_type = delivery
status = ready_for_delivery
not already assigned to an active delivery trip
```

Response should include:

```text
order_id
order_code
customer_name
customer_phone
delivery_address
delivery_latitude
delivery_longitude
geocoding_status
total_amount
payment_status
payment_method
amount_to_collect
waiting_time
created_at
```

### 10.4 Address, Geocoding, and Map Pin Flow

Delivery address input supports two modes:

```text
Default mode:
- client sends delivery_address only.
- backend geocodes delivery_address through OpenRouteService.
- backend stores delivery_latitude, delivery_longitude, formatted address,
  place_id, geocoded_at, geocoding_status, and map_provider.

Pick-on-map mode:
- client still sends delivery_address for display/instructions.
- client also sends delivery_latitude and delivery_longitude from a map pin.
- backend trusts the provided coordinates as the confirmed delivery location.
- backend stores delivery_address as descriptive text.
```

Important validation:

```text
- If both delivery_latitude and delivery_longitude are provided, use them.
- If neither coordinate is provided, geocode delivery_address.
- If only one coordinate is provided, reject as delivery_coordinates_incomplete.
- If geocoding fails or is ambiguous, reject the order and ask the client to
  correct the address or pick a pin.
```

Map provider configuration:

```text
MAPS_PROVIDER=openrouteservice
OPENROUTESERVICE_API_KEY=<api key>
MAPS_REQUEST_TIMEOUT_SECONDS=8
```

OpenRouteService usage:

```text
- Geocoding endpoint: /geocode/search
- Matrix endpoint: /v2/matrix/driving-car
- Geocoding returns coordinates as [longitude, latitude].
- Backend stores them as delivery_latitude and delivery_longitude.
```

### 10.5 Auto Batching and Exact Route Optimization

Auto batching is a recommendation flow, not full autopilot. The backend suggests
batches, then delivery manager creates the trip.

Batch suggestion input:

```text
- all ready_for_delivery orders, or a manager-selected order_ids subset.
- max_orders_per_trip, hard capped at 12.
```

Batching rule:

```text
1. Exclude orders already assigned to an active trip.
2. Require delivery coordinates.
3. Pick the oldest waiting order as the seed.
4. Add nearby orders to that seed.
5. Apply a waiting-time bonus so older orders are not left behind.
6. Stop when max_orders_per_trip is reached.
7. Repeat until queue is grouped.
```

Routing rule inside each batch:

```text
1. Build coordinates list: shop first, then delivery stops.
2. Use OpenRouteService Matrix to get driving distance and duration between all points.
3. Run exact TSP with Held-Karp dynamic programming.
4. Optimize primarily by total duration.
5. Use total distance as tie-breaker.
6. Do not add a return-to-shop leg after the last stop.
```

Route output:

```text
- ordered stops
- distance_from_previous_km for each stop
- duration_from_previous_minutes for each stop
- total_distance_km
- total_duration_minutes
- route_provider
```

Exact TSP limit:

```text
max_orders_per_trip = 12
```

The cap is a maximum, not a target. A trip can contain 1 to 12 orders. If the
manager selects 3 orders, exact TSP runs on those 3 orders only.

Fallback for local testing:

```text
If the map provider API key is missing for route matrix calls, backend may use
Haversine fallback for local/test routing. Production routing should use the
configured map provider.
```

Provider behavior:

```text
If OPENROUTESERVICE_API_KEY is configured:
- route_provider should be openrouteservice.
- total_distance_km and total_duration_minutes come from ORS driving matrix.

If OPENROUTESERVICE_API_KEY is missing in local/test:
- route_provider may be haversine_fallback.
- route ordering still works, but distance/duration are estimates.
```

### 10.6 Create Trip Flow

Endpoint:

```http
POST /api/v1/deliveries/trips
```

Request:

```json
{
  "order_ids": ["uuid1", "uuid2", "uuid3"],
  "use_auto_route": true
}
```

Flow:

```text
1. Validate current user is admin or delivery_manager.
2. Validate all orders exist.
3. Validate all orders are delivery orders.
4. Validate all orders are ready_for_delivery.
5. Validate orders are not already assigned to active trip.
6. Validate orders have coordinates.
7. If use_auto_route = true:
   - reject more than 12 stops.
   - build route matrix with map provider.
   - calculate stop_order with exact TSP.
   - calculate total_distance_km and total_duration_minutes.
8. Else:
   - use request order sequence.
   - route metrics may be stored as manual/zero until recalculated.
9. Calculate expected_cod_amount:
   - sum total_amount for COD/unpaid orders.
10. Insert delivery_trips row:
   - include total_distance_km, total_duration_minutes, route_provider.
11. Insert delivery_trip_orders rows:
   - include stop_order, distance_from_previous_km, duration_from_previous_minutes.
12. Commit.
```

Route snapshot rule:

```text
Trip route metrics are stored when the trip is created. Later edits to the
order address must not silently change an already-created trip route.
```

### 10.7 Assign Shipper Flow

```text
1. Validate trip exists.
2. Validate trip status = pending_dispatch.
3. Validate staff exists and role = shipper.
4. Validate shipper is active.
5. Optional: validate shipper has no active trip.
6. Set trip.shipper_id.
7. Set trip.status = assigned.
8. Commit.
```

### 10.8 Start Trip Flow

```text
1. Validate current user is assigned shipper.
2. Validate trip status = assigned.
3. Set status = in_transit.
4. Set started_at = now.
5. Commit.
```

### 10.9 Location Update Flow

Purpose:

```text
Allow delivery manager to track where the assigned shipper currently is while
the trip is in_transit.
```

Responsibility split:

```text
Shipper client:
- asks for device location permission.
- reads GPS/current position from browser or mobile OS.
- sends latitude/longitude to backend every configured interval.

Backend:
- validates shipper and trip state.
- stores every location update as an event log.
- returns the newest location log in manager trip detail.

Manager client:
- polls trip detail periodically.
- reads latest_location.
- renders or moves the shipper marker on the map.
```

Endpoint:

```http
POST /api/v1/shipper/trips/{trip_id}/location
```

Request:

```json
{
  "latitude": 21.027763,
  "longitude": 105.834160,
  "recorded_at": "2026-06-07T14:10:00+07:00"
}
```

Shipper client location source:

```text
Web client:
- use navigator.geolocation.getCurrentPosition for one-time location updates.
- or use navigator.geolocation.watchPosition for continuous updates.

Mobile app:
- use the platform location service.
- send the same latitude/longitude payload to the backend.
```

Shipper update loop:

```text
1. Shipper opens assigned trip.
2. Shipper starts trip.
3. Trip status becomes in_transit.
4. Shipper client requests location permission.
5. If permission is granted:
   - read current latitude/longitude from device GPS/location service.
   - POST location to backend.
   - repeat every SHIPPER_LOCATION_UPDATE_INTERVAL_SECONDS while trip is in_transit.
6. If permission is denied:
   - show client-side error.
   - keep manual location update or retry permission as fallback.
```

Backend validation flow:

```text
1. Validate current user is assigned shipper.
2. Validate trip status = in_transit.
3. Validate latitude and longitude are valid.
4. Use request recorded_at when provided, otherwise use server time.
5. Insert delivery_location_logs row with trip_id, shipper_id, latitude,
   longitude, and recorded_at.
6. Commit.
```

Manager tracking flow:

```http
GET /api/v1/deliveries/trips/{trip_id}
```

```text
1. Manager opens trip detail.
2. Manager client polls trip detail every 10-30 seconds.
3. Backend returns latest_location from delivery_location_logs ordered by
   recorded_at desc.
4. If latest_location is null, no location update has been received yet.
5. If latest_location exists, manager client displays the shipper marker at
   latest_location.latitude/latest_location.longitude and shows recorded_at.
```

Response field:

```json
{
  "latest_location": {
    "latitude": "10.7768890",
    "longitude": "106.7008060",
    "recorded_at": "2026-06-07T14:10:00+07:00"
  }
}
```

Version 1 tracking mode:

```text
Use REST polling.
Do not require WebSocket/SSE for v1.
WebSocket/SSE can be added later to push location changes to manager clients,
but the shipper client still must send GPS updates to the backend.
```

### 10.10 Mark Delivered Flow

```text
1. Validate current user is assigned shipper.
2. Validate trip status = in_transit.
3. Validate order belongs to trip.
4. Validate delivery_trip_order status = assigned.
5. If order payment method is COD or payment_status is unpaid:
   - require cod_collected == order.total_amount.
   - create/update payment with method = cod, status = success.
   - set order.payment_status = paid.
6. If order is prepaid:
   - require cod_collected = 0.
7. Set delivery_trip_order.status = delivered.
8. Set delivered_at = now.
9. Add cod_collected and optional note.
10. Complete the order transaction.
11. If all orders in trip are delivered or failed:
   - set trip.status = completed.
   - set completed_at = now.
12. Commit.
```

Important:

For delivery COD orders, inventory and finance completion can happen after successful delivery. The service should call order completion logic after payment is confirmed and delivery is delivered.

### 10.11 Mark Failed Flow

```text
1. Validate current user is assigned shipper.
2. Validate trip status = in_transit.
3. Validate order belongs to trip.
4. Set delivery_trip_order.status = failed.
5. Save failed_reason, failed_at, and optional note.
6. Return order to delivery queue:
   - order.status = ready_for_delivery
   - order.payment_status remains unpaid if COD
7. If all trip orders are delivered or failed:
   - set trip.status = completed.
8. Commit.
```

### 10.12 COD Reconciliation Flow

Endpoint:

```http
POST /api/v1/deliveries/trips/{trip_id}/reconcile
```

Request:

```json
{
  "actual_amount": 250000,
  "discrepancy_reason": "Customer paid less due to missing item"
}
```

Flow:

```text
1. Validate current user is delivery_manager or admin.
2. Validate trip status = completed.
3. Calculate expected_amount from delivered COD orders.
4. Calculate discrepancy = actual_amount - expected_amount.
5. If discrepancy != 0:
   - require discrepancy_reason.
   - status = flagged_for_review.
6. Else:
   - status = confirmed.
7. Insert cod_reconciliations row.
8. Update trip:
   - actual_cod_amount
   - discrepancy_amount
   - discrepancy_reason
   - status = reconciled
   - reconciled_at = now
9. Create financial record if needed.
10. Commit.
```

### 10.13 Delivery Done When

- Delivery manager can view ready delivery orders.
- Delivery orders can be geocoded from address.
- Backend can accept map-picked coordinates when client sends lat/lon.
- Delivery manager can request auto batch suggestions.
- Backend can exact-optimize route stops with max 12 stops.
- Backend stores route snapshot metrics on trips and stops.
- Delivery manager can create trip from selected orders.
- Delivery manager can assign shipper.
- Shipper can start trip.
- Shipper can update location.
- Manager can view latest shipper location for a trip.
- Shipper can mark delivered or failed.
- COD collection updates payment.
- COD reconciliation works.

---

## Phase 11 — Finance and Dashboard

### Goal

Expose financial summary and operational dashboard APIs.

### Finance Endpoints

```http
GET  /api/v1/finance/summary?month=2026-05
GET  /api/v1/finance/expenses?month=2026-05
POST /api/v1/finance/expenses
GET  /api/v1/finance/records?month=2026-05
```

### Dashboard Endpoints

```http
GET /api/v1/dashboard/today
GET /api/v1/dashboard/low-stock
GET /api/v1/dashboard/best-selling-products?month=2026-05
GET /api/v1/dashboard/delivery-performance?month=2026-05
```

### Dashboard Implementation Status

```text
Implemented.
```

The dashboard APIs no longer return mock data. They are backed by the
existing finance, order, inventory, product, and delivery tables.

Access:

```text
Required roles:
- admin
- delivery_manager
```

Business date behavior:

```text
Dashboard day/month windows use the configured shop timezone.
Default shop_timezone = Asia/Ho_Chi_Minh
The backend converts local business windows to UTC for timestamp queries.
```

Current dashboard data rules:

```text
GET /api/v1/dashboard/today
- date: local shop date
- revenue: sum financial_records.amount where record_type = revenue,
  source_type = order, and financial_records.created_at is inside today
- order_count: non-deleted orders created today
- completed_order_count: non-deleted completed orders completed today
- delivery_queue_count: delivery orders ready_for_delivery with no active trip assignment
- low_stock_count: ingredients where current_stock <= minimum_threshold

GET /api/v1/dashboard/low-stock
- Returns low-stock ingredients using the same shape as ingredient low-stock reads.
- Excludes soft-deleted ingredients.

GET /api/v1/dashboard/best-selling-products?month=YYYY-MM
- Counts completed, non-deleted orders by completed_at month.
- Groups by product.
- quantity_sold = sum(order_items.quantity)
- revenue = sum(order_items.line_total)
- Sorts by quantity_sold desc, then revenue desc.
- Product-level revenue does not allocate order discounts.

GET /api/v1/dashboard/delivery-performance?month=YYYY-MM
- total_trips: non-deleted trips created in the month
- completed_trips: completed or reconciled trips completed in the month
- average_delivery_minutes: average completed_at - started_at in minutes,
  using trips that have both timestamps
- cod_pending: sum expected_cod_amount for completed but unreconciled trips
```

Backend implementation files:

```text
backend/app/api/v1/dashboard.py
backend/app/services/dashboard_service.py
backend/app/repositories/dashboard_repo.py
backend/app/schemas/dashboard.py
```

Dashboard API testing guide:

```text
backend/docs/api-testing-dashboard-swagger.md
```

### Finance Summary Formula

```text
Revenue = sum(financial_records where record_type = revenue)
Material Cost = sum(financial_records where record_type = material_cost)
Operating Expense = sum(financial_records where record_type = operating_expense)
Net Profit = Revenue - Material Cost - Operating Expense
```

### Add Expense Flow

```text
1. Validate amount > 0.
2. Insert expenses row.
3. Insert financial_records row:
   - record_type = operating_expense
   - source_type = expense
   - source_id = expenses.id
   - amount = expense.amount
4. Commit.
```

### Done when

- Finance summary works by month.
- Expense recording updates finance ledger.
- Dashboard can show today revenue, order count, completed order count,
  delivery queue count, and low-stock count.
- Dashboard can list low-stock ingredients.
- Dashboard can list best-selling products by completed-order month.
- Dashboard can show delivery performance by month.
- Dashboard endpoints are protected for admin and delivery_manager users.

---

## Phase 12 — Reporting Views, Optional

Do not implement this until basic reporting APIs work.

If queries become complex, create PostgreSQL views:

```text
reporting.daily_revenue
reporting.monthly_profit
reporting.best_selling_products
reporting.inventory_consumption
reporting.delivery_performance
```

If views are slow, convert heavy ones to materialized views.

---

## 8. API Permission Matrix

| Module | Admin | Inventory Manager | Delivery Manager | Cashier | Shipper |
|---|---:|---:|---:|---:|---:|
| Auth | Yes | Yes | Yes | Yes | Yes |
| Account Management | Yes | No | No | No | No |
| Staff Management | Yes | No | No | No | No |
| Product/Menu | Yes | Yes | View | View active | No |
| Inventory | Yes | Yes | No | No | No |
| Orders | Yes | No | View delivery | Yes | Assigned only |
| Payments | Yes | No | COD only | Yes | COD collect |
| Delivery | Yes | No | Yes | Create delivery order | Assigned trips |
| Finance | Yes | Limited/View | COD summary | No | No |
| Customer | Yes | No | No | Yes/limited | No |
| Dashboard | Yes | Limited | Limited | Limited | No |

---

## 9. Testing Plan

### 9.1 Unit Tests

Test business logic without HTTP.

Required tests:

```text
Auth:
- Password hashing works
- Invalid password rejected
- Role permission works

Order:
- Order total calculation
- Invalid empty order rejected
- Invalid status transition rejected
- Delivery order can geocode coordinates from address
- Delivery order rejects incomplete coordinate pair
- Delivery order uses map-picked lat/lon when both coordinates are provided
- Delivery order cannot be marked ready without delivery info
- Unpaid delivery order requires COD pending or payment_method = cod
- Prepaid delivery order can be marked ready after card/bank payment

Payment:
- Cash payment calculates change
- Cash payment rejects insufficient amount
- Cash payment is rejected for delivery orders
- COD payment is rejected for in-store orders
- COD delivery payment is pending until delivery succeeds
- Mock card approval works
- Mock bank amount mismatch rejected

Inventory:
- Purchase increases stock
- Low-stock detection works
- Stock cannot become negative

Recipe:
- Product recipe quantity validation
- Missing ingredient rejected

Order completion:
- Completed order deducts stock
- Insufficient stock rolls back order completion
- Financial records created

Delivery:
- Haversine fallback distance calculation for local/test route matrix
- OpenRouteService geocode parses [longitude, latitude] correctly
- OpenRouteService matrix converts meters/seconds to km/minutes
- Exact TSP route ordering
- Batch suggestion enforces max 12 stops
- Auto batch suggestion groups nearby orders while considering waiting time
- Trip creation stores route snapshot metrics
- Shipper location update requires assigned shipper and in_transit trip
- Shipper location update stores latitude, longitude, and recorded_at
- Latest trip location returns newest location log
- Manager trip detail includes latest_location when logs exist
- Manager trip detail returns latest_location = null before first update
- Trip creation validates order status
- Failed delivery returns order to queue
- Delivered COD order marks COD payment success
- Delivered prepaid order requires cod_collected = 0
- COD reconciliation discrepancy requires reason

Finance:
- Revenue/material/expense/net profit calculation
```

### 9.2 Integration Tests

Test full API flows.

Flow 1:

```text
Login admin
Create ingredient
Create product category
Create product with recipe
Create order
Pay cash
Complete order
Check inventory deducted
Check financial records created
```

Flow 2:

```text
Create delivery order
Start processing
Mark ready_for_delivery with COD pending or prepaid payment
Create delivery trip
Assign shipper
Start trip
Mark delivered with COD
Reconcile COD
```

Flow 3:

```text
Record purchase
Check inventory stock
Check inventory movement
Check purchase history
```

### 9.3 Test Coverage Target

Minimum target:

```text
70% coverage for service/business logic
```

---

## 10. Git Workflow for 3 People

### 10.1 Branching

Use this branch model:

```text
main          stable only
dev           integration branch
feature/...   individual feature branches
fix/...       bug fix branches
```

Examples:

```text
feature/auth-rbac
feature/inventory
feature/orders-payments
feature/delivery-routing
fix/order-completion-rollback
```

### 10.2 Pull Request Rules

A PR can be merged only if:

```text
- Code runs locally
- Migration is included if models changed
- Tests added or updated
- No formatting/lint error
- No direct business logic inside route file
- At least one teammate reviews it
```

### 10.3 Commit Message Style

Use simple conventional commits:

```text
feat: add product recipe model
fix: prevent negative stock after order completion
refactor: move order logic into service
 test: add cash payment tests
chore: update docker compose
```

---

## 11. Team Task Arrangement

The team has 3 people. Split by domain ownership, but everyone must follow the same structure and review each other's code.

## Person 1 — Core/Auth/Staff/Project Structure Lead

Primary responsibility:

```text
Foundation, authentication, RBAC, account/staff management, code consistency
```

Tasks:

```text
Phase 0:
- Create FastAPI project structure
- Configure Docker Compose
- Configure PostgreSQL connection
- Configure Alembic
- Create response/error helpers
- Create lint/format setup

Phase 1:
- Create base model
- Create users model
- Create staff_profiles model
- Create staff_tasks model
- Create audit_logs model

Phase 2:
- Implement login
- Implement JWT
- Implement password hashing
- Implement current user dependency
- Implement role permission dependency

Phase 3:
- Implement account CRUD
- Implement staff CRUD
- Implement staff task APIs

Support:
- Review all PRs for project structure consistency
- Maintain README and .env.example
- Make sure all routes follow standard response format
```

Deliverables:

```text
Auth works
RBAC works
Admin can manage accounts and staff
Project structure remains unified
```

## Person 2 — Product/Inventory/Order/Payment Lead

Primary responsibility:

```text
Product catalog, recipe/BOM, inventory, order creation, payment, order completion transaction
```

Tasks:

```text
Phase 1:
- Create product_categories model
- Create products model
- Create ingredients model
- Create product_recipes model
- Create orders model
- Create order_items model
- Create payments model
- Create inventory_purchases model
- Create inventory_movements model

Phase 4:
- Implement ingredient CRUD
- Implement purchase recording
- Implement inventory movement ledger
- Implement low-stock API

Phase 5:
- Implement category CRUD
- Implement product CRUD
- Implement product recipe create/update
- Implement availability toggle
- Implement product delete restriction

Phase 6:
- Implement create order using customer lookup/create before order insert
- Implement order list/detail/filter
- Implement status transition validation
- Implement cancel order

Phase 7:
- Implement cash payment
- Implement mock card payment
- Implement mock bank transfer
- Implement COD payment placeholder

Phase 8:
- Implement complete order transaction
- Implement inventory deduction
- Implement material cost calculation
- Implement financial record creation for completed order
```

Deliverables:

```text
Inventory works
Menu and recipe works
Orders can be created
Payments work
Completing order deducts inventory and records finance
```

Important warning:

Person 2 owns the most critical transaction in the system. This code must be heavily tested and reviewed by Person 1 and Person 3.

## Person 3 — Delivery/Finance/Dashboard/Reporting Lead

Primary responsibility:

```text
Delivery workflow, routing algorithm, COD reconciliation, finance dashboard, reporting APIs
```

Tasks:

```text
Phase 1:
- Create delivery_trips model
- Create delivery_trip_orders model
- Create delivery_location_logs model
- Create cod_reconciliations model
- Create expenses model
- Create financial_records model

Phase 10:
- Implement delivery queue
- Implement map/geocoding service for delivery addresses
- Implement OpenRouteService geocoding and route matrix integration
- Implement manual trip creation
- Implement exact TSP route ordering with max 12 stops
- Implement batch suggestion by nearby location and waiting time
- Store route snapshot metrics on trips and trip stops
- Implement assign shipper
- Implement start trip
- Implement shipper client location update endpoint
- Implement latest trip location query
- Document shipper client periodic GPS update responsibility
- Document manager client trip-detail polling responsibility
- Implement mark delivered
- Implement mark failed
- Implement COD reconciliation

Phase 11:
- Implement expense API [done]
- Implement finance summary API [done]
- Implement dashboard today API [done]
- Implement best-selling product API [done]
- Implement delivery performance API [done]

Phase 12:
- Add reporting views only if needed
```

Deliverables:

```text
Delivery manager can batch and assign orders
Shipper can complete delivery flow
COD reconciliation works
Finance and dashboard APIs work
```

Dashboard handoff notes:

```text
Dashboard endpoints are implemented and protected by role.
Allowed roles: admin, delivery_manager.

Frontend should call:
- GET /api/v1/dashboard/today
- GET /api/v1/dashboard/low-stock
- GET /api/v1/dashboard/best-selling-products?month=YYYY-MM
- GET /api/v1/dashboard/delivery-performance?month=YYYY-MM

All responses use the standard wrapper:
{
  "success": true,
  "message": "Fetched successfully",
  "data": ...
}

Dashboard date/month calculations use shop local time.
Default shop_timezone = Asia/Ho_Chi_Minh.

Best-selling products are based on completed orders only.
Delivery pending COD is based on completed but unreconciled trips.

Swagger testing doc:
backend/docs/api-testing-dashboard-swagger.md
```

Delivery routing and tracking notes:

```text
Routing:
- Use OpenRouteService Matrix for driving distance and duration.
- Use backend exact TSP for stop ordering.
- Keep 12 stops as the hard cap for exact TSP.

Tracking:
- Shipper client gets GPS from device/browser location service.
- Shipper client sends location updates periodically while trip is in_transit.
- Backend stores location logs and exposes latest_location.
- Manager client polls trip detail to display the current shipper marker.
```

---

## 12. Final Backend Build Order

Build in this exact order:

```text
1. Project setup
2. Database models and migration
3. Auth and RBAC
4. Account/staff
5. Inventory
6. Product/menu/recipe
7. Customer management
8. Orders
9. Payments
10. Complete order + inventory deduction + finance records
11. Delivery queue
12. Trip creation and route ordering
13. Shipper assignment and delivery status
14. COD reconciliation
15. Finance dashboard
16. Reporting APIs
17. Tests and stabilization
```

Do not start with auto-routing first. Auto-routing depends on delivery orders, coordinates, trips, and shipper assignment. Build those foundations first.
