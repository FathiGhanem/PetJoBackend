"""Add status tracking to advertisements

Revision ID: add_advertisement_status
Revises: previous_revision
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_advertisement_status'
down_revision = None  # Update this with your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add status, admin_notes, updated_at, and reviewed_at to advertisements table."""
    
    # Add new columns
    op.add_column('advertisements', 
        sa.Column('status', sa.Text(), nullable=False, server_default='pending')
    )
    op.add_column('advertisements', 
        sa.Column('admin_notes', sa.Text(), nullable=True)
    )
    op.add_column('advertisements', 
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('advertisements', 
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Make user_id NOT NULL if it wasn't already
    op.alter_column('advertisements', 'user_id',
        existing_type=postgresql.UUID(),
        nullable=False
    )
    
    # Make title and description NOT NULL
    op.alter_column('advertisements', 'title',
        existing_type=sa.Text(),
        nullable=False
    )
    op.alter_column('advertisements', 'description',
        existing_type=sa.Text(),
        nullable=False
    )
    
    # Create indexes
    op.create_index('idx_advertisement_user', 'advertisements', ['user_id'])
    op.create_index('idx_advertisement_status', 'advertisements', ['status'])
    op.create_index('idx_advertisement_created', 'advertisements', ['created_at'])


def downgrade() -> None:
    """Remove the added columns and indexes."""
    
    # Drop indexes
    op.drop_index('idx_advertisement_created', table_name='advertisements')
    op.drop_index('idx_advertisement_status', table_name='advertisements')
    op.drop_index('idx_advertisement_user', table_name='advertisements')
    
    # Drop columns
    op.drop_column('advertisements', 'reviewed_at')
    op.drop_column('advertisements', 'updated_at')
    op.drop_column('advertisements', 'admin_notes')
    op.drop_column('advertisements', 'status')
    
    # Revert nullable changes
    op.alter_column('advertisements', 'description',
        existing_type=sa.Text(),
        nullable=True
    )
    op.alter_column('advertisements', 'title',
        existing_type=sa.Text(),
        nullable=True
    )
    op.alter_column('advertisements', 'user_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )
