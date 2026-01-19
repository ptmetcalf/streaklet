"""Add icon field to household_tasks

Revision ID: 009
Revises: 008
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Add icon column (nullable) to household_tasks table
    # Stores Material Design Icon name (e.g., 'broom', 'leaf', 'wrench')
    op.add_column('household_tasks', sa.Column('icon', sa.String(), nullable=True))


def downgrade():
    op.drop_column('household_tasks', 'icon')
