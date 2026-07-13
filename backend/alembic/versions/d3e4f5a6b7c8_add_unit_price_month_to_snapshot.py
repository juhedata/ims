"""add unit_price and snapshot_month to inventory_item_snapshot

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-06-14 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_item_snapshot",
        sa.Column("snapshot_month", sa.String(length=7), nullable=True, comment="快照所属月份，格式 YYYY-MM"),
    )
    op.add_column(
        "inventory_item_snapshot",
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=True, comment="采购单价"),
    )
    op.create_index(
        op.f("ix_inventory_item_snapshot_snapshot_month"),
        "inventory_item_snapshot",
        ["snapshot_month"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_inventory_item_snapshot_snapshot_month"),
        table_name="inventory_item_snapshot",
    )
    op.drop_column("inventory_item_snapshot", "unit_price")
    op.drop_column("inventory_item_snapshot", "snapshot_month")
