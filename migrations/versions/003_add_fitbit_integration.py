"""add fitbit integration

Revision ID: 003
Revises: 002
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create fitbit_connections table
    op.create_table(
        'fitbit_connections',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('fitbit_user_id', sa.String(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('connected_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], name='fk_fitbit_connections_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_fitbit_connections_fitbit_user_id'), 'fitbit_connections', ['fitbit_user_id'], unique=True)
    op.create_index(op.f('ix_fitbit_connections_user_id'), 'fitbit_connections', ['user_id'], unique=False)

    # 2. Create fitbit_metrics table
    op.create_table(
        'fitbit_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('metric_type', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], name='fk_fitbit_metrics_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fitbit_metrics_user_id'), 'fitbit_metrics', ['user_id'], unique=False)
    op.create_index(op.f('ix_fitbit_metrics_date'), 'fitbit_metrics', ['date'], unique=False)
    op.create_index(op.f('ix_fitbit_metrics_metric_type'), 'fitbit_metrics', ['metric_type'], unique=False)
    op.create_index('ix_fitbit_metrics_user_date_type', 'fitbit_metrics', ['user_id', 'date', 'metric_type'], unique=True)
    op.create_index('ix_fitbit_metrics_user_date', 'fitbit_metrics', ['user_id', 'date'], unique=False)

    # 3. Add Fitbit fields to tasks table (nullable, so no table recreation needed)
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fitbit_metric_type', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('fitbit_goal_value', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('fitbit_goal_operator', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('fitbit_auto_check', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.create_index(batch_op.f('ix_tasks_fitbit_metric_type'), ['fitbit_metric_type'], unique=False)


def downgrade() -> None:
    # Remove Fitbit fields from tasks
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tasks_fitbit_metric_type'))
        batch_op.drop_column('fitbit_auto_check')
        batch_op.drop_column('fitbit_goal_operator')
        batch_op.drop_column('fitbit_goal_value')
        batch_op.drop_column('fitbit_metric_type')

    # Drop fitbit_metrics table
    op.drop_index('ix_fitbit_metrics_user_date', table_name='fitbit_metrics')
    op.drop_index('ix_fitbit_metrics_user_date_type', table_name='fitbit_metrics')
    op.drop_index(op.f('ix_fitbit_metrics_metric_type'), table_name='fitbit_metrics')
    op.drop_index(op.f('ix_fitbit_metrics_date'), table_name='fitbit_metrics')
    op.drop_index(op.f('ix_fitbit_metrics_user_id'), table_name='fitbit_metrics')
    op.drop_table('fitbit_metrics')

    # Drop fitbit_connections table
    op.drop_index(op.f('ix_fitbit_connections_user_id'), table_name='fitbit_connections')
    op.drop_index(op.f('ix_fitbit_connections_fitbit_user_id'), table_name='fitbit_connections')
    op.drop_table('fitbit_connections')
