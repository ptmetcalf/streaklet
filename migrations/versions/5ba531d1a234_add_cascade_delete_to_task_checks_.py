"""add cascade delete to task_checks foreign key

Revision ID: 5ba531d1a234
Revises: 003
Create Date: 2025-12-27 19:23:49.257305

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ba531d1a234'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite doesn't support modifying foreign key constraints directly
    # Need to recreate the table with CASCADE delete on task_id FK

    # Drop temp table if it exists from failed migration
    op.execute("DROP TABLE IF EXISTS task_checks_new")

    # Create new table with CASCADE
    op.execute("""
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
    """)

    # Create index on user_id
    op.execute("CREATE INDEX ix_task_checks_new_user_id ON task_checks_new (user_id)")

    # Copy data from old table
    op.execute("""
        INSERT INTO task_checks_new (date, task_id, user_id, checked, checked_at)
        SELECT date, task_id, user_id, checked, checked_at
        FROM task_checks
    """)

    # Drop old table
    op.execute("DROP TABLE task_checks")

    # Rename new table
    op.execute("ALTER TABLE task_checks_new RENAME TO task_checks")


def downgrade() -> None:
    # Reverse: recreate without CASCADE
    op.execute("""
        CREATE TABLE task_checks_old (
            date DATE NOT NULL,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            checked BOOLEAN NOT NULL DEFAULT 0,
            checked_at DATETIME,
            PRIMARY KEY (date, task_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES profiles(id)
        )
    """)

    op.execute("CREATE INDEX ix_task_checks_old_user_id ON task_checks_old (user_id)")

    op.execute("""
        INSERT INTO task_checks_old (date, task_id, user_id, checked, checked_at)
        SELECT date, task_id, user_id, checked, checked_at
        FROM task_checks
    """)

    op.execute("DROP TABLE task_checks")
    op.execute("ALTER TABLE task_checks_old RENAME TO task_checks")
