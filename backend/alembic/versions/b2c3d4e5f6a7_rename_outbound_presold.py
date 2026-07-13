"""rename outbound_type OFFLINE_SOLD to PRESOLD

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-22 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE outbound_order SET outbound_type = 'PRESOLD' "
            "WHERE outbound_type = 'OFFLINE_SOLD'"
        )
    )
    conn.execute(
        sa.text(
            "DELETE FROM sys_enum WHERE category = 'outbound_type' AND code = 'OFFLINE_SOLD'"
        )
    )
    exists = conn.execute(
        sa.text(
            "SELECT id FROM sys_enum WHERE category = 'outbound_type' AND code = 'PRESOLD' LIMIT 1"
        )
    ).scalar()
    if not exists:
        conn.execute(
            sa.text(
                "INSERT INTO sys_enum (category, code, label, sort_order, enabled) "
                "VALUES ('outbound_type', 'PRESOLD', '准售出', 8, 1)"
            )
        )
    else:
        conn.execute(
            sa.text(
                "UPDATE sys_enum SET label = '准售出', sort_order = 8, enabled = 1 "
                "WHERE category = 'outbound_type' AND code = 'PRESOLD'"
            )
        )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE outbound_order SET outbound_type = 'OFFLINE_SOLD' "
            "WHERE outbound_type = 'PRESOLD'"
        )
    )
    conn.execute(
        sa.text("DELETE FROM sys_enum WHERE category = 'outbound_type' AND code = 'PRESOLD'")
    )
    conn.execute(
        sa.text(
            "INSERT INTO sys_enum (category, code, label, sort_order, enabled) "
            "VALUES ('outbound_type', 'OFFLINE_SOLD', '线下售出', 8, 1)"
        )
    )
