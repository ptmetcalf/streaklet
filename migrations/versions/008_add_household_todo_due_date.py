"""Add due_date to household_tasks for to-do items

Revision ID: 008
Revises: 007
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Add due_date column (nullable) to household_tasks table
    # This supports one-time "to-do" tasks with optional due dates
    op.add_column('household_tasks', sa.Column('due_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('household_tasks', 'due_date')
