"""Add Google OAuth support to users table

Revision ID: add_google_oauth
Revises: add_advertisement_status
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_google_oauth'
down_revision = 'add_advertisement_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add google_id column and make hashed_password nullable."""

    # Allow password-less (OAuth-only) accounts
    op.alter_column(
        'users', 'hashed_password',
        existing_type=sa.String(),
        nullable=True
    )

    # Add google_id for linking Google accounts
    op.add_column(
        'users',
        sa.Column('google_id', sa.String(), nullable=True)
    )
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    op.create_index('idx_users_google_id', 'users', ['google_id'])


def downgrade() -> None:
    """Remove google_id and restore hashed_password as NOT NULL."""

    op.drop_index('idx_users_google_id', table_name='users')
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    op.drop_column('users', 'google_id')

    op.alter_column(
        'users', 'hashed_password',
        existing_type=sa.String(),
        nullable=False
    )
