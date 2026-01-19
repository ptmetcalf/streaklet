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

    Note: SQLite doesn't support ALTER COLUMN or non-constant defaults when
    adding NOT NULL columns. We add as nullable, populate data, then rely on
    application-level validation.
    """
    # Step 1: Add active_since column as nullable (required for SQLite compatibility)
    op.add_column('tasks',
        sa.Column('active_since', sa.Date(), nullable=True)
    )

    # Step 2: Update existing rows to use their created_at date
    op.execute("""
        UPDATE tasks
        SET active_since = DATE(created_at)
    """)

    # Note: SQLite does not support ALTER COLUMN to add NOT NULL constraint.
    # Application code should treat NULL active_since as created_at date.


def downgrade() -> None:
    """Remove active_since field."""
    op.drop_column('tasks', 'active_since')
