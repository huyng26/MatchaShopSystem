# Database Files

Use this folder for database files that are not Alembic migrations.

- `init/*.sql`: optional raw SQL bootstrap files for first-time local setup.
- `apply-init.ps1`: applies all SQL files in `init/` to an existing PostgreSQL database.
- `migrations`: use Alembic in `backend/alembic/` for real schema evolution.
