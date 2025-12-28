"""fix task_checks cascade if needed

Revision ID: 1e1ad4c2e340
Revises: 5ba531d1a234
Create Date: 2025-12-27 20:52:58.257443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e1ad4c2e340'
down_revision = '5ba531d1a234'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Safely fix task_checks table to have CASCADE delete.
    This migration detects the current state and only applies fixes if needed.
    Safe to run on any database state (fresh, broken, or already fixed).
    """
    conn = op.get_bind()

    # Clean up any leftover temp tables from failed migrations
    conn.execute(sa.text("DROP TABLE IF EXISTS task_checks_new"))
    conn.execute(sa.text("DROP TABLE IF EXISTS task_checks_old"))

    # Check if task_checks exists and needs CASCADE fix
    # Query SQLite's schema to check foreign key constraints
    result = conn.execute(sa.text(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='task_checks'"
    )).fetchone()

    if not result:
        # Table doesn't exist - let the previous migration handle it
        return

    table_sql = result[0]

    # Check if CASCADE is already present
    if 'ON DELETE CASCADE' in table_sql:
        # Already fixed, nothing to do
        return

    # Need to apply CASCADE fix
    # Create new table with CASCADE
    conn.execute(sa.text("""
        CREATE TABLE task_checks_new (
            date DATE NOT NULL,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            checked BOOLEAN NOT NULL DEFAULT 0,
            checked_at DATETIME,
            PRIMARY KEY (date, task_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES profiles(id)
        )
    """))

    # Create index on user_id
    conn.execute(sa.text("CREATE INDEX ix_task_checks_new_user_id ON task_checks_new (user_id)"))

    # Copy data from old table
    conn.execute(sa.text("""
        INSERT INTO task_checks_new (date, task_id, user_id, checked, checked_at)
        SELECT date, task_id, user_id, checked, checked_at
        FROM task_checks
    """))

    # Drop old table
    conn.execute(sa.text("DROP TABLE task_checks"))

    # Rename new table
    conn.execute(sa.text("ALTER TABLE task_checks_new RENAME TO task_checks"))


def downgrade() -> None:
    """Downgrade not supported - CASCADE is a beneficial constraint."""
    pass
