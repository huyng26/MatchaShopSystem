# Matcha Shop Backend

This backend folder is the foundation for the Matcha Shop System backend. The
main purpose of this branch is to define the initial database structure and keep
a clean project skeleton so other feature branches can branch from here.

## Branch Purpose

This branch should focus on:

- Initial PostgreSQL table structure.
- Minimal FastAPI application skeleton.
- Minimal database connection setup.
- Mock API endpoints for early frontend integration.
- Folder and file structure for all backend modules.
- A stable base branch for feature branches.

This branch should not contain real business features yet. Feature branches
should branch from here to replace mock API behavior with real APIs, business
logic, tests, and migrations for each module.

Recommended branch flow:

```text
backend
  feature/auth-rbac
  feature/products-inventory
  feature/orders-payments
  feature/delivery
  feature/finance-dashboard
```

## Tech Stack

```text
Framework: FastAPI
Database: PostgreSQL
Database driver: asyncpg
ORM: SQLAlchemy async
Migration tool: Alembic
Validation: Pydantic
Testing: Pytest
Container: Docker
```

## Main Structure

```text
backend/
  app/
    api/v1/
    core/
    models/
    schemas/
    services/
    repositories/
    utils/
    seed/
  alembic/
  db/init/
  tests/
  .env.example
  Dockerfile
  main.py
  pyproject.toml
  requirements.txt
```

## Environment Files

This project uses two different `.env` files for two different purposes.

### Root `.env`

Location:

```text
MatchaShopSystem/.env
```

Used by `docker-compose.yml`.

Current values:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=matcha_management_system
```

This file controls the local Docker Postgres container. It does not configure
the FastAPI app directly.

Template:

```text
MatchaShopSystem/.env.example
```

### Backend `.env`

Location:

```text
backend/.env
```

Used by the FastAPI backend container through `env_file`.

Current local Docker database URL:

```env
DATABASE_URL=postgresql+asyncpg://admin:password@db:5432/matcha_management_system
```

For a PostgreSQL host shared through Tailscale, change only `DATABASE_URL`:

```env
DATABASE_URL=postgresql+asyncpg://DB_USER:DB_PASSWORD@100.93.151.127:5432/matcha_management_system
```

Template:

```text
backend/.env.example
```

## Root Files

### Root `.env.example`

Template for Docker Compose environment variables.

Important values:

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

Do not commit real `.env` files.

### `Dockerfile`

Builds the backend container.

It installs dependencies from `requirements.txt`, copies backend code into the
image, and starts FastAPI with Uvicorn.

### `main.py`

Top-level app entrypoint used by Docker and Uvicorn.

It imports the real FastAPI app from:

```text
app/main.py
```

This keeps the command simple:

```bash
uvicorn main:app --reload
```

### `requirements.txt`

Python dependencies for the backend.

Current important packages:

```text
fastapi
uvicorn
sqlalchemy
asyncpg
alembic
pydantic
pydantic-settings
pytest
ruff
```

### `pyproject.toml`

Tool configuration.

Currently used for:

```text
ruff
pytest
```

## Application Entry

### `app/main.py`

Creates the FastAPI app.

Current responsibilities:

- Create `FastAPI(title="Matcha Shop Backend")`.
- Register `/health`.
- Include the API v1 router under `/api/v1`.
- Dispose database connections when the app shuts down.

Current endpoints:

```http
GET /health
GET /api/v1/status
GET /api/v1/status/db
POST /api/v1/auth/login
POST /api/v1/auth/token
POST /api/v1/auth/refresh
GET /api/v1/auth/me
GET /api/v1/accounts
POST /api/v1/accounts
GET /api/v1/accounts/{user_id}
PUT /api/v1/accounts/{user_id}
DELETE /api/v1/accounts/{user_id}
GET /api/v1/staff
POST /api/v1/staff
GET /api/v1/staff/{staff_id}
PUT /api/v1/staff/{staff_id}
DELETE /api/v1/staff/{staff_id}
```

Auth, account, and staff APIs are backed by services and the database. Other
domain modules may still expose lightweight mock endpoints until their feature
phases replace them with service calls.

## API Layer

Folder:

```text
app/api/v1/
```

This folder contains FastAPI route files. Route files should stay thin. They
should receive requests, validate dependencies, call services, and return
responses. Business logic should not live here.

### `app/api/v1/router.py`

Central router for API version 1.

Every route module must be registered here.

Example later:

```python
api_router.include_router(products.router, prefix="/products", tags=["products"])
```

### `app/api/v1/status.py`

Basic status endpoints.

```http
GET /api/v1/status
GET /api/v1/status/db
```

`/status/db` calls the database ping function to confirm the backend can connect
to PostgreSQL.

### Route Files

These files define the module API boundaries:

```text
auth.py          login, refresh token, logout, current user
accounts.py      user account management
staff.py         staff profile and staff task APIs
customers.py     customer CRUD and customer order history
products.py      product category, product, recipe APIs
ingredients.py   ingredient, purchase, inventory movement APIs
orders.py        order creation, status, completion APIs
payments.py      cash, card, bank transfer, COD payment APIs
deliveries.py    queue, trip, shipper, COD reconciliation APIs
finance.py       expense and finance ledger APIs
dashboard.py     dashboard/reporting APIs
```

Person 1 modules (`auth.py`, `accounts.py`, `staff.py`) use real schemas,
services, repositories, RBAC dependencies, and the standard response format.

## Core Layer

Folder:

```text
app/core/
```

This folder contains shared application infrastructure.

### `config.py`

Reads environment variables.

Current responsibilities:

- Define `Settings`.
- Read `.env` if present.
- Expose `get_settings()`.

Main setting:

```text
database_url
```

### `database.py`

Owns database connectivity.

Current responsibilities:

- Create async SQLAlchemy engine.
- Create async session factory.
- Provide `get_db()` dependency for FastAPI routes.
- Provide `ping_database()` for DB health check.
- Dispose the engine on shutdown.

Routes/services should use `get_db()` instead of creating their own connection.

### `constants.py`

Reserved for shared constants and enum-like values used across modules.

Examples later:

```text
Role names
Order statuses
Payment statuses
Default page size
```

### `exceptions.py`

Reserved for custom application exceptions and global exception handlers.

Examples later:

```text
NotFoundError
PermissionDeniedError
BusinessRuleError
```

### `permissions.py`

Reserved for role-based access control dependencies.

Examples later:

```text
require_roles("admin")
require_roles("admin", "cashier")
```

### `responses.py`

Reserved for standard API response helpers.

Target success format:

```json
{
  "success": true,
  "message": "Fetched successfully",
  "data": {}
}
```

### `security.py`

Reserved for authentication utilities.

Examples later:

```text
Password hashing
Password verification
JWT creation
JWT decoding
```

## Model Layer

Folder:

```text
app/models/
```

This folder will contain SQLAlchemy ORM models. The raw SQL schema already
exists under `db/init/`; ORM models should match those tables.

### `base.py`

Defines the shared SQLAlchemy declarative base:

```python
class Base(DeclarativeBase):
    pass
```

All ORM models should inherit from `Base`.

### Model Placeholder Files

```text
user.py       users
staff.py      staff_profiles
customer.py   customers
product.py    product_categories, products
inventory.py  ingredients, product_recipes, inventory_purchases, inventory_movements
order.py      orders, order_items
payment.py    payments
delivery.py   delivery_trips, delivery_trip_orders, delivery_location_logs, cod_reconciliations
finance.py    expenses, financial_records
audit.py      audit_logs
```

## Schema Layer

Folder:

```text
app/schemas/
```

This folder will contain Pydantic schemas for request and response validation.

Schemas should not contain database logic.

### Schema Placeholder Files

```text
auth.py       login/token schemas
account.py    user account request/response schemas
staff.py      staff and task schemas
customer.py   customer schemas
product.py    category, product, recipe schemas
inventory.py  ingredient, purchase, movement schemas
order.py      order and order item schemas
payment.py    payment schemas
delivery.py   delivery queue, trip, COD schemas
finance.py    expense and finance schemas
common.py     shared response and pagination schemas
```

## Service Layer

Folder:

```text
app/services/
```

This folder contains business logic. Services should coordinate validation,
repositories, transactions, and cross-module workflows.

Route files should call services instead of implementing business rules directly.

### Service Placeholder Files

```text
auth_service.py       login, token, current user logic
account_service.py    account management logic
staff_service.py      staff and task logic
customer_service.py   customer logic
product_service.py    product and recipe logic
inventory_service.py  purchase, stock, movement logic
order_service.py      order creation, status, completion logic
payment_service.py    payment processing logic
delivery_service.py   delivery queue, trip, COD logic
routing_service.py    distance and route ordering logic
finance_service.py    expense and finance summary logic
dashboard_service.py  dashboard/reporting logic
```

Important rule:

```text
Any operation that changes multiple tables should be handled in a service inside
one database transaction.
```

## Repository Layer

Folder:

```text
app/repositories/
```

This folder contains database query helpers. Repositories should hide complex
SQLAlchemy queries from services.

Simple CRUD may start in services, but once queries become complex or reused,
move them into repositories.

### Repository Placeholder Files

```text
user_repo.py
staff_repo.py
customer_repo.py
product_repo.py
inventory_repo.py
order_repo.py
payment_repo.py
delivery_repo.py
finance_repo.py
```

## Utilities

Folder:

```text
app/utils/
```

Small reusable helpers that do not belong to a specific business module.

### Utility Placeholder Files

```text
pagination.py    page/page_size helpers
datetime.py      timezone/date helpers
money.py         money rounding/format helpers
id_generator.py  order_code/trip_code generation helpers
distance.py      Haversine distance and routing helpers
```

## Seed Data

Folder:

```text
app/seed/
```

Reserved for local development seed data.

### `seed_data.py`

Creates or reactivates a default admin account and matching staff profile for
local development.

```text
SEED_ADMIN_EMAIL=admin@matcha.local
SEED_ADMIN_PASSWORD=Admin12345
SEED_ADMIN_PHONE=0900000001
```

Run after the database tables exist:

```bash
docker compose run --rm backend python -m app.seed.seed_data
```

Do not put production data here.

## Database Bootstrap SQL

Folder:

```text
db/init/
```

This folder contains raw SQL files mounted into the Postgres Docker container.
Postgres runs these files only when the database volume is created for the first
time.

Important distinction:

```text
docker compose up creates tables automatically only for the Postgres container
defined as the db service in docker-compose.yml, and only when its Docker volume
is created for the first time.
```

If the backend connects to an existing PostgreSQL database hosted on Windows,
Tailscale, pgAdmin, DBeaver, or another machine, Docker Compose will not create
tables in that database automatically. In that case, run the SQL files manually
with `db/apply-init.ps1`.

The files are split by purpose and run in filename order.

### `001_extensions.sql`

Creates PostgreSQL extensions.

Current extension:

```sql
pgcrypto
```

Used for `gen_random_uuid()`.

### `002_types.sql`

Creates enum types used by the schema.

Examples:

```text
user_role
user_status
order_status
payment_method
delivery_trip_status
```

### `003_functions.sql`

Creates shared database functions.

Current function:

```text
set_updated_at()
```

Used by triggers to update `updated_at`.

### `010_identity_customers.sql`

Creates identity and customer-related tables:

```text
users
staff_profiles
customers
```

### `020_catalog_inventory.sql`

Creates product and inventory-related tables:

```text
product_categories
products
ingredients
product_recipes
inventory_purchases
inventory_movements
```

### `030_orders_payments.sql`

Creates POS order and payment tables:

```text
orders
order_items
payments
```

### `040_finance_delivery_audit.sql`

Creates finance, delivery, COD, and audit tables:

```text
expenses
financial_records
delivery_trips
delivery_trip_orders
delivery_location_logs
cod_reconciliations
audit_logs
```

### `090_indexes.sql`

Creates indexes for common filtering and joins.

Examples:

```text
orders.status
orders.created_at
payments.order_id
delivery_trips.status
financial_records.record_date
```

### `099_triggers.sql`

Creates `updated_at` triggers for tables that have an `updated_at` column.

## Apply SQL To An Existing PostgreSQL Host

Use this when PostgreSQL already exists and only the database is empty.

Script:

```text
backend/db/apply-init.ps1
```

If `psql` is installed on Windows:

```powershell
.\backend\db\apply-init.ps1 `
  -DatabaseUrl "postgresql://admin:password@localhost:5432/matcha_management_system"
```

If `psql` is not installed, use Docker to run the `psql` client:

```powershell
.\backend\db\apply-init.ps1 `
  -DatabaseUrl "postgresql://admin:password@host.docker.internal:5432/matcha_management_system" `
  -UseDocker
```

For the shared Tailscale database:

```powershell
.\backend\db\apply-init.ps1 `
  -DatabaseUrl "postgresql://DB_USER:DB_PASSWORD@100.93.151.127:5432/matcha_management_system" `
  -UseDocker
```

Use `localhost` when running `psql` directly on Windows. Use
`host.docker.internal` when the `psql` client runs inside Docker and needs to
reach PostgreSQL on the Windows host.

After applying the SQL, check tables with:

```powershell
psql "postgresql://admin:password@localhost:5432/matcha_management_system" -c "\dt"
```

or in a GUI tool such as DBeaver, pgAdmin, or DataGrip.

## Alembic

Folder:

```text
alembic/
```

Alembic is for schema migrations after the base schema is created.

Current files:

```text
alembic.ini
alembic/env.py
alembic/script.py.mako
alembic/README
```

For this base branch, raw SQL bootstrap files are the main schema source. Once
feature branches start changing models, use Alembic migrations to track schema
changes.

## Tests

Folder:

```text
tests/
  unit/
  integration/
```

### `tests/unit/`

For isolated business logic tests.

Examples later:

```text
Password verification
Order total calculation
Route ordering
Finance summary calculation
```

### `tests/integration/`

For full API/database flow tests.

Examples later:

```text
Create product
Create order
Record payment
Complete order
Deduct inventory
```

## How To Run

From the project root:

```bash
docker compose up --build
```

Before running, copy environment templates:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
```

Then choose the database mode in `backend/.env`.

For each teammate's local Docker database:

```env
DATABASE_URL=postgresql+asyncpg://admin:password@db:5432/matcha_management_system
```

For the shared PostgreSQL database through Tailscale:

```env
DATABASE_URL=postgresql+asyncpg://DB_USER:DB_PASSWORD@100.93.151.127:5432/matcha_management_system
```

Run mode:

```powershell
# Local database container + backend
docker compose up --build

# Backend only, when DATABASE_URL points to the shared Tailscale database
docker compose up --build backend
```

Create the first local admin account:

```powershell
docker compose run --rm backend python -m app.seed.seed_data
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Basic checks:

```text
http://localhost:8000/health
http://localhost:8000/api/v1/status
http://localhost:8000/api/v1/status/db
```

Run backend checks:

```powershell
docker compose run --rm backend pytest
docker compose run --rm backend ruff check .
```

## Recreate Local Database

The SQL files in `db/init/` only run when the Postgres volume is created for the
first time.

If the local database has no important data and you want to apply the bootstrap
SQL from scratch:

```bash
docker compose down -v
docker compose up --build
```

Do not run `down -v` if the local database contains data you need.

## Using A Remote PostgreSQL Host Through Tailscale

Backend code does not need to change.

Set `DATABASE_URL` in `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://DB_USER:DB_PASSWORD@100.93.151.127:5432/matcha_management_system
```

or with Tailscale MagicDNS:

```env
DATABASE_URL=postgresql+asyncpg://DB_USER:DB_PASSWORD@db-host.tailnet-name.ts.net:5432/matcha_management_system
```

Make sure the PostgreSQL host allows connections from Tailscale:

```text
Postgres listens on the Tailscale interface
pg_hba.conf allows the client
Firewall allows port 5432
Database user/password are correct
```

The SQL bootstrap files will not run automatically on this remote database.
Apply them with `backend/db/apply-init.ps1` or run the files manually in a DB
GUI tool.

## How Frontend Connects

Frontend should call the backend API, not PostgreSQL directly.

Local backend API base URL:

```text
http://localhost:8000/api/v1
```

Remote backend API base URL over Tailscale:

```text
http://100.x.x.x:8000/api/v1
```

Frontend environment example:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## How To Add A New API Module

Example: products.

1. Add route handlers in:

```text
app/api/v1/products.py
```

2. Register the router in:

```text
app/api/v1/router.py
```

3. Add request/response schemas in:

```text
app/schemas/product.py
```

4. Add business logic in:

```text
app/services/product_service.py
```

5. Add reusable DB queries in:

```text
app/repositories/product_repo.py
```

6. Add ORM models in:

```text
app/models/product.py
```

7. Add tests in:

```text
tests/unit/
tests/integration/
```

## Coding Rules For Feature Branches

- API routes stay thin.
- Business logic goes in services.
- Reusable/complex queries go in repositories.
- Schemas validate request/response data.
- ORM models must match database tables.
- Frontend never connects directly to PostgreSQL.
- Every protected route must check user role.
- Every multi-table write must use one database transaction.
- Important business records should use soft delete with `deleted_at`.
- Schema changes after this base should use Alembic migrations.

## Current Scope Status

Done in this base:

```text
Backend folder skeleton
FastAPI entrypoint
Health/status endpoints
Async database connection setup
Raw SQL bootstrap split by purpose
Docker Postgres init mount
Person 1 ORM models: users, staff_profiles, audit_logs
Person 1 Pydantic schemas
JWT login, refresh token, current user dependency
Password hashing with bcrypt
Admin RBAC dependency
Account CRUD APIs
Staff profile CRUD APIs
Audit log writes for account/staff changes
Standard API response and error handlers
Alembic metadata wiring for implemented ORM models
Admin seed script
Focused unit tests for security and responses
```

Not done yet:

```text
Full ORM models for Person 2 and Person 3 domains
Full Pydantic schemas for Person 2 and Person 3 domains
Real business APIs outside auth/account/staff
Alembic migration revisions
Integration tests with a real PostgreSQL database
Frontend integration
```
