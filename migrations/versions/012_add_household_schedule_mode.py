"""add household schedule mode and biweekly

Revision ID: 012
Revises: 011
Create Date: 2026-01-21
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    # Add schedule_mode and next_due_date columns
    op.add_column('household_tasks', sa.Column('schedule_mode', sa.String(), nullable=True))
    op.add_column('household_tasks', sa.Column('next_due_date', sa.Date(), nullable=True))

    # Set default schedule_mode to 'calendar' for existing tasks
    op.execute("""
        UPDATE household_tasks
        SET schedule_mode = 'calendar'
        WHERE schedule_mode IS NULL
    """)

    # For SQLite: Cannot directly alter ENUM, but we can work around it
    # SQLite stores ENUMs as strings with CHECK constraints
    # We need to recreate the table to add 'biweekly' to the frequency options

    # Step 1: Create new table with updated schema
    op.execute("""
        CREATE TABLE household_tasks_new (
            id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            description VARCHAR,
            frequency VARCHAR NOT NULL CHECK(frequency IN ('weekly', 'biweekly', 'monthly', 'quarterly', 'annual', 'todo')),
            due_date DATE,
            icon VARCHAR,
            schedule_mode VARCHAR,
            recurrence_day_of_week INTEGER,
            recurrence_day_of_month INTEGER,
            recurrence_month INTEGER,
            recurrence_day INTEGER,
            next_due_date DATE,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Step 2: Copy data from old table
    op.execute("""
        INSERT INTO household_tasks_new (
            id, title, description, frequency, due_date, icon, schedule_mode,
            recurrence_day_of_week, recurrence_day_of_month, recurrence_month,
            recurrence_day, next_due_date, sort_order, is_active, created_at, updated_at
        )
        SELECT
            id, title, description, frequency, due_date, icon, schedule_mode,
            recurrence_day_of_week, recurrence_day_of_month, recurrence_month,
            recurrence_day, next_due_date, sort_order, is_active, created_at, updated_at
        FROM household_tasks
    """)

    # Step 3: Drop old table
    op.execute("DROP TABLE household_tasks")

    # Step 4: Rename new table
    op.execute("ALTER TABLE household_tasks_new RENAME TO household_tasks")

    # Step 5: Recreate indexes
    op.execute("CREATE INDEX ix_household_tasks_frequency ON household_tasks(frequency)")
    op.execute("CREATE INDEX ix_household_tasks_next_due_date ON household_tasks(next_due_date)")


def downgrade():
    # Recreate original table without biweekly, schedule_mode, and next_due_date
    op.execute("""
        CREATE TABLE household_tasks_old (
            id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            description VARCHAR,
            frequency VARCHAR NOT NULL CHECK(frequency IN ('weekly', 'monthly', 'quarterly', 'annual', 'todo')),
            due_date DATE,
            icon VARCHAR,
            recurrence_day_of_week INTEGER,
            recurrence_day_of_month INTEGER,
            recurrence_month INTEGER,
            recurrence_day INTEGER,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Copy data back (biweekly tasks will be lost, rolling tasks reset to calendar)
    op.execute("""
        INSERT INTO household_tasks_old (
            id, title, description, frequency, due_date, icon,
            recurrence_day_of_week, recurrence_day_of_month, recurrence_month,
            recurrence_day, sort_order, is_active, created_at, updated_at
        )
        SELECT
            id, title, description,
            CASE WHEN frequency = 'biweekly' THEN 'weekly' ELSE frequency END,
            due_date, icon,
            recurrence_day_of_week, recurrence_day_of_month, recurrence_month,
            recurrence_day, sort_order, is_active, created_at, updated_at
        FROM household_tasks
        WHERE frequency != 'biweekly' OR frequency IS NULL
    """)

    op.execute("DROP TABLE household_tasks")
    op.execute("ALTER TABLE household_tasks_old RENAME TO household_tasks")
    op.execute("CREATE INDEX ix_household_tasks_frequency ON household_tasks(frequency)")
