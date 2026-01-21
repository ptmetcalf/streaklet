"""add household calendar recurrence

Revision ID: 010
Revises: d0ab11d85464
Create Date: 2026-01-20
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = 'd0ab11d85464'
branch_labels = None
depends_on = None


def upgrade():
    # Add recurrence configuration columns for calendar-based scheduling
    op.add_column('household_tasks', sa.Column('recurrence_day_of_week', sa.Integer(), nullable=True))
    op.add_column('household_tasks', sa.Column('recurrence_day_of_month', sa.Integer(), nullable=True))
    op.add_column('household_tasks', sa.Column('recurrence_month', sa.Integer(), nullable=True))
    op.add_column('household_tasks', sa.Column('recurrence_day', sa.Integer(), nullable=True))

    # Set default values for existing tasks based on their frequency
    # Weekly tasks: default to Monday (0)
    op.execute("""
        UPDATE household_tasks
        SET recurrence_day_of_week = 0
        WHERE frequency = 'weekly' AND recurrence_day_of_week IS NULL
    """)

    # Monthly tasks: default to 1st of month
    op.execute("""
        UPDATE household_tasks
        SET recurrence_day_of_month = 1
        WHERE frequency = 'monthly' AND recurrence_day_of_month IS NULL
    """)

    # Quarterly tasks: default to 1st day of 1st month of quarter (Jan 1, Apr 1, Jul 1, Oct 1)
    op.execute("""
        UPDATE household_tasks
        SET recurrence_month = 1, recurrence_day = 1
        WHERE frequency = 'quarterly' AND recurrence_month IS NULL
    """)

    # Annual tasks: default to January 1st
    op.execute("""
        UPDATE household_tasks
        SET recurrence_month = 1, recurrence_day = 1
        WHERE frequency = 'annual' AND (recurrence_month IS NULL OR recurrence_day IS NULL)
    """)


def downgrade():
    op.drop_column('household_tasks', 'recurrence_day')
    op.drop_column('household_tasks', 'recurrence_month')
    op.drop_column('household_tasks', 'recurrence_day_of_month')
    op.drop_column('household_tasks', 'recurrence_day_of_week')
