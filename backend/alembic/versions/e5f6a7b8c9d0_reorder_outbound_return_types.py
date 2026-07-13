"""reorder outbound types and split return conditions

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-22 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # 旧「售出-线下」出库实际走准售出流程，单品在 PRESOLD 状态
    conn.execute(
        sa.text(
            """
            UPDATE outbound_order o
            SET outbound_type = 'PRESOLD'
            WHERE o.outbound_type = 'SOLD_OFFLINE'
              AND EXISTS (
                SELECT 1
                FROM outbound_order_item ooi
                JOIN inventory_item ii ON ii.id = ooi.item_id
                WHERE ooi.outbound_order_id = o.id
                  AND ii.stock_status = 'PRESOLD'
              )
            """
        )
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE outbound_order SET outbound_type = 'SOLD_OFFLINE' "
            "WHERE outbound_type = 'PRESOLD'"
        )
    )
