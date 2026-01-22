"""add schedule mode to tasks

Revision ID: 011
Revises: 010
Create Date: 2026-01-21
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Add schedule_mode column for scheduled tasks
    # 'calendar' = fixed dates/days (e.g., every Tuesday)
    # 'rolling' = interval-based from completion (e.g., every 7 days from completion)
    op.add_column('tasks', sa.Column('schedule_mode', sa.String(), nullable=True))

    # Default existing scheduled tasks to 'calendar' mode for backward compatibility
    op.execute("""
        UPDATE tasks
        SET schedule_mode = 'calendar'
        WHERE task_type = 'scheduled' AND schedule_mode IS NULL
    """)


def downgrade():
    op.drop_column('tasks', 'schedule_mode')
