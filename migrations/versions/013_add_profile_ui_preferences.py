"""add profile ui preferences

Revision ID: 013
Revises: 012
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa


revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'profiles',
        sa.Column('confetti_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1'))
    )
    op.add_column(
        'profiles',
        sa.Column('show_shopping_list', sa.Boolean(), nullable=False, server_default=sa.text('0'))
    )


def downgrade():
    op.drop_column('profiles', 'show_shopping_list')
    op.drop_column('profiles', 'confetti_enabled')
