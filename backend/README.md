# Backend Skeleton

This folder is the shared backend base for feature branches.

## Branch Purpose

This branch is the backend foundation branch. Its main scope is:

- Define the initial database table structure.
- Keep the project skeleton consistent for all backend developers.
- Provide minimal database connection setup.
- Serve as the checkout base for feature branches.

Feature branches should branch from here to implement business logic, API
details, tests, and migrations for each module.

## Structure

```text
backend/
  app/
    api/v1/          REST route modules
    core/            config, database, security, permissions, responses
    models/          SQLAlchemy ORM models
    schemas/         Pydantic request/response schemas
    services/        business logic
    repositories/    database query helpers
    utils/           small shared utilities
    seed/            seed scripts
  alembic/           database migrations
  db/init/           optional raw SQL bootstrap files
  tests/             unit and integration tests
```

## Raw SQL Location

Put first-time database bootstrap SQL in:

```text
backend/db/init/
```

The files are split by purpose and run in filename order:

```text
001_extensions.sql
002_types.sql
003_functions.sql
010_identity_customers.sql
020_catalog_inventory.sql
030_orders_payments.sql
040_finance_delivery_audit.sql
090_indexes.sql
099_triggers.sql
```

When mounted into the Postgres container, `.sql` files in this folder run only
when the database volume is created for the first time. After the project starts
using Alembic, migrations should be the main source of schema changes.

## Database Connection

The shared async SQLAlchemy connection is defined in:

```text
app/core/database.py
```

Use `get_db()` as the FastAPI dependency for routes and services that need a
database session.

The basic DB health check endpoint is:

```http
GET /api/v1/status/db
```

If the Docker database volume already exists, changes in `db/init/*.sql` will
not run automatically. Recreate the volume for a fresh local database, or apply
schema changes through Alembic once migrations are introduced.
