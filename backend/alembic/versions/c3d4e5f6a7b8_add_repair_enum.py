"""add repair stock status and outbound type

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-22 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


NEW_ENUMS = [
    ("stock_status", "REPAIR", "维修", 11),
    ("stock_condition", "RETURNED_FROM_REPAIR", "维修退回", 9),
    ("outbound_type", "REPAIR", "维修", 9),
    ("inbound_type", "RETURNED_FROM_REPAIR", "维修退回", 9),
]


def _insert_enums(conn) -> None:
    for category, code, label, sort_order in NEW_ENUMS:
        exists = conn.execute(
            sa.text(
                "SELECT id FROM sys_enum WHERE category = :category AND code = :code LIMIT 1"
            ),
            {"category": category, "code": code},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO sys_enum (category, code, label, sort_order, enabled) "
                "VALUES (:category, :code, :label, :sort_order, 1)"
            ),
            {
                "category": category,
                "code": code,
                "label": label,
                "sort_order": sort_order,
            },
        )


def _delete_enums(conn) -> None:
    for category, code, _, _ in NEW_ENUMS:
        conn.execute(
            sa.text("DELETE FROM sys_enum WHERE category = :category AND code = :code"),
            {"category": category, "code": code},
        )


def upgrade():
    conn = op.get_bind()
    _insert_enums(conn)


def downgrade():
    conn = op.get_bind()
    _delete_enums(conn)
