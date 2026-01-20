"""add_icon_to_tasks

Revision ID: d0ab11d85464
Revises: 009
Create Date: 2026-01-19 16:38:12.889285

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0ab11d85464'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add icon column to tasks table (nullable, for Material Design Icons)
    op.add_column('tasks', sa.Column('icon', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove icon column from tasks table
    op.drop_column('tasks', 'icon')
