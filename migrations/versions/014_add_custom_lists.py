"""add custom lists and migrate shopping list tasks

Revision ID: 014
Revises: 013
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa


revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "custom_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("template_key", sa.String(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"]),
        sa.UniqueConstraint("user_id", "name", name="uq_custom_lists_user_name"),
        sa.UniqueConstraint("user_id", "template_key", name="uq_custom_lists_user_template_key"),
    )
    op.create_index("ix_custom_lists_user_id", "custom_lists", ["user_id"])

    op.add_column("tasks", sa.Column("custom_list_id", sa.Integer(), nullable=True))
    op.create_index("ix_tasks_custom_list_id", "tasks", ["custom_list_id"])

    conn = op.get_bind()
    profiles = [row[0] for row in conn.execute(sa.text("SELECT id FROM profiles")).fetchall()]

    for profile_id in profiles:
        conn.execute(sa.text(
            "INSERT INTO custom_lists (user_id, name, icon, template_key, is_enabled, sort_order) "
            "VALUES (:user_id, 'Shopping', 'cart-outline', 'shopping', 1, 1)"
        ), {"user_id": profile_id})
        conn.execute(sa.text(
            "INSERT INTO custom_lists (user_id, name, icon, template_key, is_enabled, sort_order) "
            "VALUES (:user_id, 'Grocery', 'basket-outline', 'grocery', 0, 2)"
        ), {"user_id": profile_id})
        conn.execute(sa.text(
            "INSERT INTO custom_lists (user_id, name, icon, template_key, is_enabled, sort_order) "
            "VALUES (:user_id, 'Xmas List', 'gift-outline', 'xmas', 0, 3)"
        ), {"user_id": profile_id})

    conn.execute(sa.text(
        "UPDATE tasks "
        "SET task_type='custom_list', "
        "    custom_list_id=("
        "        SELECT id FROM custom_lists "
        "        WHERE custom_lists.user_id = tasks.user_id AND custom_lists.template_key = 'shopping' "
        "        LIMIT 1"
        "    ), "
        "    is_required=0 "
        "WHERE task_type='shopping_list'"
    ))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE tasks "
        "SET task_type='shopping_list', custom_list_id=NULL "
        "WHERE task_type='custom_list'"
    ))

    op.drop_index("ix_tasks_custom_list_id", table_name="tasks")
    op.drop_column("tasks", "custom_list_id")

    op.drop_index("ix_custom_lists_user_id", table_name="custom_lists")
    op.drop_table("custom_lists")
