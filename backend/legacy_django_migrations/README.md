# Legacy Django Migrations (Historical Archive)

This directory contains the historical Django migration files preserved for schema audit and database lineage evidence.

Prior to the FastAPI migration, database schemas were managed by Django migrations. As of milestone `bdb7e77e43d1`, all future database schema migrations are managed authoritatively by Alembic (`backend/alembic/`).

These files are inactive historical artifacts and are not executed at runtime.
