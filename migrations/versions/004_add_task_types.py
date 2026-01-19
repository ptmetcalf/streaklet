"""add task types and scheduling

Revision ID: 004
Revises: 003
Create Date: 2026-01-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '004'
down_revision = '1e1ad4c2e340'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add task type and scheduling fields to tasks table
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # Discriminator (all existing tasks become 'daily')
        batch_op.add_column(sa.Column('task_type', sa.String(), nullable=False, server_default='daily'))

        # Punch list fields
        batch_op.add_column(sa.Column('due_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))

        # Scheduled task fields
        batch_op.add_column(sa.Column('recurrence_pattern', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('last_occurrence_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('next_occurrence_date', sa.Date(), nullable=True))

        # Indexes
        batch_op.create_index('ix_tasks_task_type', ['task_type'], unique=False)
        batch_op.create_index('ix_tasks_due_date', ['due_date'], unique=False)
        batch_op.create_index('ix_tasks_next_occurrence_date', ['next_occurrence_date'], unique=False)


def downgrade() -> None:
    # Remove task type and scheduling fields
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_index('ix_tasks_next_occurrence_date')
        batch_op.drop_index('ix_tasks_due_date')
        batch_op.drop_index('ix_tasks_task_type')

        batch_op.drop_column('next_occurrence_date')
        batch_op.drop_column('last_occurrence_date')
        batch_op.drop_column('recurrence_pattern')
        batch_op.drop_column('archived_at')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('due_date')
        batch_op.drop_column('task_type')
