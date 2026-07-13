"""add offline sale stock status and outbound type

Revision ID: a1b2c3d4e5f6
Revises: f9a0b1c2d3e4
Create Date: 2026-06-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f9a0b1c2d3e4"
branch_labels = None
depends_on = None


NEW_ENUMS = [
    ("stock_status", "PRESOLD", "准售出", 9),
    ("stock_status", "SOLD_OFFLINE", "线下已售", 10),
    ("stock_condition", "RETURNED_FROM_PRESOLD", "准售出退回", 8),
    ("outbound_type", "PRESOLD", "准售出", 8),
    ("inbound_type", "RETURNED_FROM_PRESOLD", "准售出退回", 8),
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
