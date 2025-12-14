"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)

    op.create_table(
        'daily_status',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('date')
    )

    op.create_table(
        'task_checks',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('checked', sa.Boolean(), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('date', 'task_id')
    )


def downgrade() -> None:
    op.drop_table('task_checks')
    op.drop_table('daily_status')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
