"""Add active_since to tasks

Revision ID: 006
Revises: 005
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa
from datetime import date


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add active_since field to tasks table.

    This field tracks when a task becomes active for completion tracking.
    Only counts toward daily completion on dates >= active_since.

    Note: SQLite doesn't support ALTER COLUMN, so we add the column with
    a default value directly.
    """
    # Add active_since column with default for new rows
    # SQLite will use DATE('now') for any new inserts
    op.add_column('tasks',
        sa.Column('active_since', sa.Date(), nullable=False,
                  server_default=sa.text("DATE('now')"))
    )

    # Update existing rows to use their created_at date
    op.execute("""
        UPDATE tasks
        SET active_since = DATE(created_at)
    """)


def downgrade() -> None:
    """Remove active_since field."""
    op.drop_column('tasks', 'active_since')
