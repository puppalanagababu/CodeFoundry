"""initialize application schema

Revision ID: c8b1a4f02e9d
Revises: bdb7e77e43d1
Create Date: 2026-09-29 23:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8b1a4f02e9d'
down_revision: Union[str, None] = 'bdb7e77e43d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MANAGED_TABLES = {
    'users_user',
    'challenges_challenge',
    'challenges_testcase',
    'challenges_challengefile',
    'submissions_submission',
    'evaluations_evaluation',
    'evaluations_achievement',
    'evaluations_userachievement',
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names()) & MANAGED_TABLES

    # CASE A: Existing Database (All 8 application tables already exist)
    if len(existing_tables) == len(MANAGED_TABLES):
        # Database was already initialized by pre-migration baseline.
        # Perform zero DDL and allow Alembic to record this revision as head.
        return

    # CASE C: Partially Initialized Database (Corrupted / incomplete state)
    if 0 < len(existing_tables) < len(MANAGED_TABLES):
        missing_tables = MANAGED_TABLES - existing_tables
        raise RuntimeError(
            f"ABORTING MIGRATION: Database is in an ambiguous partially initialized state! "
            f"Found {len(existing_tables)} of {len(MANAGED_TABLES)} managed tables: {sorted(list(existing_tables))}. "
            f"Missing {len(missing_tables)} tables: {sorted(list(missing_tables))}. "
            f"Manual investigation or backup recovery is required."
        )

    # CASE B: Completely Fresh Database (0 application tables exist)
    # 1. users_user
    op.create_table(
        'users_user',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('password', sa.String(length=128), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('first_name', sa.String(length=150), nullable=False),
        sa.Column('last_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('is_staff', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('date_joined', sa.DateTime(timezone=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='users_user_username_key'),
    )

    # 2. challenges_challenge
    op.create_table(
        'challenges_challenge',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('challenge_type', sa.String(length=20), nullable=False),
        sa.Column('programming_language', sa.String(length=50), nullable=False),
        sa.Column('starter_code', sa.Text(), nullable=False),
        sa.Column('entrypoint', sa.String(length=255), nullable=False),
        sa.Column('time_limit', sa.Integer(), nullable=False),
        sa.Column('memory_limit', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='challenges_challenge_slug_key'),
    )

    # 3. evaluations_achievement
    op.create_table(
        'evaluations_achievement',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='evaluations_achievement_code_key'),
    )

    # 4. challenges_testcase
    op.create_table(
        'challenges_testcase',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('challenge_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('is_hidden', sa.Boolean(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges_challenge.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 5. challenges_challengefile
    op.create_table(
        'challenges_challengefile',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('challenge_id', sa.BigInteger(), nullable=False),
        sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_test', sa.Boolean(), nullable=False),
        sa.Column('is_readonly', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges_challenge.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('challenge_id', 'path', name='challenges_challengefile_challenge_id_path_c5c8d203_uniq'),
    )

    # 6. evaluations_userachievement
    op.create_table(
        'evaluations_userachievement',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('achievement_id', sa.BigInteger(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['evaluations_achievement.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='evaluations_userachievem_user_id_achievement_id_2816cf1a_uniq'),
    )

    # 7. submissions_submission
    op.create_table(
        'submissions_submission',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('challenge_id', sa.BigInteger(), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('files', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=False),
        sa.Column('memory_used', sa.Float(), nullable=False),
        sa.Column('test_results', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges_challenge.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 8. evaluations_evaluation
    op.create_table(
        'evaluations_evaluation',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('submission_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('tests_total', sa.Integer(), nullable=False),
        sa.Column('tests_passed', sa.Integer(), nullable=False),
        sa.Column('tests_failed', sa.Integer(), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=False),
        sa.Column('memory_used', sa.Float(), nullable=False),
        sa.Column('stdout', sa.Text(), nullable=False),
        sa.Column('stderr', sa.Text(), nullable=False),
        sa.Column('test_results', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('skill_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions_submission.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', name='evaluations_evaluation_submission_id_key'),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names()) & MANAGED_TABLES

    # Only drop if all managed tables are present to avoid partial destruction
    if len(existing_tables) == len(MANAGED_TABLES):
        op.drop_table('evaluations_evaluation')
        op.drop_table('submissions_submission')
        op.drop_table('evaluations_userachievement')
        op.drop_table('challenges_challengefile')
        op.drop_table('challenges_testcase')
        op.drop_table('evaluations_achievement')
        op.drop_table('challenges_challenge')
        op.drop_table('users_user')
