"""add dept procurement outbound type

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-06-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "i3j4k5l6m7n8"
down_revision = "h2i3j4k5l6m7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_sku_daily_ledger",
        sa.Column(
            "outbound_dept_procurement",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="出库-部门采购",
        ),
    )
    op.add_column(
        "inventory_sku_daily_ledger",
        sa.Column(
            "inbound_returned_from_dept_procurement",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="入库-部门采购退回",
        ),
    )


def downgrade():
    op.drop_column("inventory_sku_daily_ledger", "inbound_returned_from_dept_procurement")
    op.drop_column("inventory_sku_daily_ledger", "outbound_dept_procurement")
