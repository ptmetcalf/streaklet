"""add fitbit preferences

Revision ID: 005
Revises: 004
Create Date: 2026-01-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create fitbit_preferences table
    op.create_table(
        'fitbit_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),

        # Metric visibility toggles
        sa.Column('show_steps', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_distance', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_floors', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_calories', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_active_minutes', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_sleep', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_sleep_stages', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_heart_rate', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_hrv', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_cardio_fitness', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_breathing_rate', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_spo2', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_temperature', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_weight', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('show_body_fat', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('show_water', sa.Boolean(), nullable=False, server_default='0'),

        # Custom goals (nullable = use defaults)
        sa.Column('goal_steps', sa.Integer(), nullable=True),
        sa.Column('goal_active_minutes', sa.Integer(), nullable=True),
        sa.Column('goal_sleep_hours', sa.Float(), nullable=True),
        sa.Column('goal_water_oz', sa.Integer(), nullable=True),
        sa.Column('goal_weekly_steps', sa.Integer(), nullable=True),

        # Dashboard preferences
        sa.Column('default_tab', sa.String(), nullable=False, server_default='overview'),
        sa.Column('chart_preferences', sa.JSON(), nullable=True),

        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], name='fk_fitbit_preferences_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_fitbit_preferences_user_id')
    )
    op.create_index(op.f('ix_fitbit_preferences_user_id'), 'fitbit_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_fitbit_preferences_user_id'), table_name='fitbit_preferences')
    op.drop_table('fitbit_preferences')
