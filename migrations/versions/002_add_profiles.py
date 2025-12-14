"""add profiles and user_id

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False, server_default='#3b82f6'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'], unique=False)
    op.create_index(op.f('ix_profiles_name'), 'profiles', ['name'], unique=True)

    # 2. Insert default profile
    op.execute(
        "INSERT INTO profiles (id, name, color, created_at, updated_at) "
        "VALUES (1, 'Default Profile', '#3b82f6', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )

    # 3. For tasks - SQLite doesn't support ALTER COLUMN, so recreate the table
    connection = op.get_bind()
    existing_tasks = connection.execute(sa.text(
        "SELECT id, title, sort_order, is_required, is_active, created_at, updated_at FROM tasks"
    )).fetchall()

    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')

    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], name='fk_tasks_user_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)

    # Restore tasks with user_id = 1
    for row in existing_tasks:
        connection.execute(sa.text(
            "INSERT INTO tasks (id, user_id, title, sort_order, is_required, is_active, created_at, updated_at) "
            "VALUES (:id, 1, :title, :sort_order, :is_required, :is_active, :created_at, :updated_at)"
        ), {
            "id": row[0],
            "title": row[1],
            "sort_order": row[2],
            "is_required": row[3],
            "is_active": row[4],
            "created_at": row[5],
            "updated_at": row[6]
        })

    # 4. For task_checks - also recreate the table
    existing_checks = connection.execute(sa.text(
        "SELECT date, task_id, checked, checked_at FROM task_checks"
    )).fetchall()

    op.drop_table('task_checks')

    op.create_table(
        'task_checks',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('checked', sa.Boolean(), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], name='fk_task_checks_user_id'),
        sa.PrimaryKeyConstraint('date', 'task_id')
    )
    op.create_index(op.f('ix_task_checks_user_id'), 'task_checks', ['user_id'], unique=False)

    # Restore task_checks with user_id = 1
    for row in existing_checks:
        date_val = row[0] if isinstance(row[0], str) else row[0].strftime('%Y-%m-%d')
        checked_at_val = f"'{row[3]}'" if row[3] else 'NULL'
        connection.execute(sa.text(
            f"INSERT INTO task_checks (date, task_id, user_id, checked, checked_at) "
            f"VALUES ('{date_val}', {row[1]}, 1, {row[2]}, {checked_at_val})"
        ))

    # 5. For daily_status, we need to drop and recreate with composite PK
    # Data already saved in connection variable
    existing_daily_status = connection.execute(sa.text("SELECT date, completed_at FROM daily_status")).fetchall()

    # Drop the old table
    op.drop_table('daily_status')

    # Create new table with composite primary key
    op.create_table(
        'daily_status',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('date', 'user_id')
    )
    op.create_index(op.f('ix_daily_status_user_id'), 'daily_status', ['user_id'], unique=False)

    # Restore data with user_id = 1
    for row in existing_daily_status:
        date_str = row[0] if isinstance(row[0], str) else row[0].strftime('%Y-%m-%d')
        completed_at = f"'{row[1]}'" if row[1] else 'NULL'
        op.execute(
            f"INSERT INTO daily_status (date, user_id, completed_at) "
            f"VALUES ('{date_str}', 1, {completed_at})"
        )


def downgrade() -> None:
    connection = op.get_bind()

    # Drop daily_status and recreate without user_id
    existing_daily_status = connection.execute(
        sa.text("SELECT date, completed_at FROM daily_status WHERE user_id = 1")
    ).fetchall()

    op.drop_index(op.f('ix_daily_status_user_id'), table_name='daily_status')
    op.drop_table('daily_status')

    op.create_table(
        'daily_status',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('date')
    )

    for row in existing_daily_status:
        date_str = row[0] if isinstance(row[0], str) else row[0].strftime('%Y-%m-%d')
        completed_at = f"'{row[1]}'" if row[1] else 'NULL'
        connection.execute(sa.text(
            f"INSERT INTO daily_status (date, completed_at) "
            f"VALUES ('{date_str}', {completed_at})"
        ))

    # Recreate task_checks without user_id
    existing_checks = connection.execute(sa.text(
        "SELECT date, task_id, checked, checked_at FROM task_checks WHERE user_id = 1"
    )).fetchall()

    op.drop_index(op.f('ix_task_checks_user_id'), table_name='task_checks')
    op.drop_table('task_checks')

    op.create_table(
        'task_checks',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('checked', sa.Boolean(), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('date', 'task_id')
    )

    for row in existing_checks:
        date_val = row[0] if isinstance(row[0], str) else row[0].strftime('%Y-%m-%d')
        checked_at_val = f"'{row[3]}'" if row[3] else 'NULL'
        connection.execute(sa.text(
            f"INSERT INTO task_checks (date, task_id, checked, checked_at) "
            f"VALUES ('{date_val}', {row[1]}, {row[2]}, {checked_at_val})"
        ))

    # Recreate tasks without user_id
    existing_tasks = connection.execute(sa.text(
        "SELECT id, title, sort_order, is_required, is_active, created_at, updated_at FROM tasks WHERE user_id = 1"
    )).fetchall()

    op.drop_index(op.f('ix_tasks_user_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')

    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)

    for row in existing_tasks:
        connection.execute(sa.text(
            "INSERT INTO tasks (id, title, sort_order, is_required, is_active, created_at, updated_at) "
            "VALUES (:id, :title, :sort_order, :is_required, :is_active, :created_at, :updated_at)"
        ), {
            "id": row[0],
            "title": row[1],
            "sort_order": row[2],
            "is_required": row[3],
            "is_active": row[4],
            "created_at": row[5],
            "updated_at": row[6]
        })

    # Drop profiles table
    op.drop_index(op.f('ix_profiles_name'), table_name='profiles')
    op.drop_index(op.f('ix_profiles_id'), table_name='profiles')
    op.drop_table('profiles')
