"""Add household maintenance tracker

Revision ID: 007
Revises: 006
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create household maintenance tracking tables.

    household_tasks: Shared tasks visible to all profiles (NO user_id FK)
    household_completions: Completion history with profile attribution
    """
    # Create household_tasks table
    op.create_table(
        'household_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('frequency', sa.Enum('weekly', 'monthly', 'quarterly', 'annual', name='household_frequency'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_household_tasks_frequency'), 'household_tasks', ['frequency'], unique=False)

    # Create household_completions table
    op.create_table(
        'household_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('household_task_id', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('completed_by_profile_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['completed_by_profile_id'], ['profiles.id'], ),
        sa.ForeignKeyConstraint(['household_task_id'], ['household_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_household_completions_completed_at'), 'household_completions', ['completed_at'], unique=False)
    op.create_index(op.f('ix_household_completions_completed_by_profile_id'), 'household_completions', ['completed_by_profile_id'], unique=False)
    op.create_index(op.f('ix_household_completions_household_task_id'), 'household_completions', ['household_task_id'], unique=False)

    # Seed default household tasks
    op.execute("""
        INSERT INTO household_tasks (title, description, frequency, sort_order) VALUES
        -- Weekly tasks
        ('Take out trash', 'Take trash and recycling bins to curb', 'weekly', 1),
        ('Vacuum floors', 'Vacuum all carpeted areas and rugs', 'weekly', 2),
        ('Clean bathrooms', 'Clean toilets, sinks, showers, and mirrors', 'weekly', 3),
        ('Mow lawn', 'Mow and edge lawn (seasonal)', 'weekly', 4),

        -- Monthly tasks
        ('Replace HVAC filter', 'Replace air conditioning/heating filter', 'monthly', 10),
        ('Deep clean kitchen', 'Clean oven, microwave, refrigerator', 'monthly', 11),
        ('Check smoke detectors', 'Test smoke and CO detectors', 'monthly', 12),
        ('Wipe down baseboards', 'Dust and wipe all baseboards', 'monthly', 13),

        -- Quarterly tasks
        ('Clean gutters', 'Remove leaves and debris from gutters', 'quarterly', 20),
        ('Wash windows', 'Clean interior and exterior windows', 'quarterly', 21),
        ('Service HVAC', 'Professional HVAC maintenance check', 'quarterly', 22),
        ('Inspect roof', 'Check for missing shingles or damage', 'quarterly', 23),

        -- Annual tasks
        ('Test sump pump', 'Test sump pump operation', 'annual', 30),
        ('Clean dryer vent', 'Remove lint buildup from dryer vent', 'annual', 31),
        ('Chimney inspection', 'Professional chimney cleaning/inspection', 'annual', 32),
        ('Pressure wash exterior', 'Pressure wash siding and deck', 'annual', 33)
    """)


def downgrade() -> None:
    """Remove household maintenance tables."""
    op.drop_index(op.f('ix_household_completions_household_task_id'), table_name='household_completions')
    op.drop_index(op.f('ix_household_completions_completed_by_profile_id'), table_name='household_completions')
    op.drop_index(op.f('ix_household_completions_completed_at'), table_name='household_completions')
    op.drop_table('household_completions')
    op.drop_index(op.f('ix_household_tasks_frequency'), table_name='household_tasks')
    op.drop_table('household_tasks')
    # Drop enum type (SQLite doesn't need this, but other DBs might)
    sa.Enum(name='household_frequency').drop(op.get_bind(), checkfirst=True)
