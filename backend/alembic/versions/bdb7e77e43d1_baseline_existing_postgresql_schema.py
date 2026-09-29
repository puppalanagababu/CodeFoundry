"""baseline existing PostgreSQL schema

Revision ID: bdb7e77e43d1
Revises: 
Create Date: 2026-09-19 20:44:20.054511

This revision represents the existing PostgreSQL schema at the point of FastAPI migration.
It is intentionally empty because the schema already exists in the live database.
It must not recreate, modify, drop, or alter existing tables, indexes, or constraints.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdb7e77e43d1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    Empty baseline migration: the PostgreSQL database schema is already established
    and managed. This revision establishes the initial Alembic version stamp without
    executing any DDL operations.
    """
    pass


def downgrade() -> None:
    """Downgrade schema.
    
    Empty baseline downgrade: does not drop or modify existing pre-migration tables.
    """
    pass
