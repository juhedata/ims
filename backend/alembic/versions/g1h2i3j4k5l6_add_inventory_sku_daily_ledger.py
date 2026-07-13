"""add inventory_sku_daily_ledger table

Revision ID: g1h2i3j4k5l6
Revises: e5f6a7b8c9d0
Create Date: 2026-06-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "g1h2i3j4k5l6"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_sku_daily_ledger",
        sa.Column("snapshot_date", sa.Date(), nullable=False, comment="业务日期"),
        sa.Column("sku_id", sa.Integer(), nullable=False, comment="SKU ID"),
        sa.Column("opening_in_stock_qty", sa.Integer(), nullable=True, comment="期初在库件数"),
        sa.Column("inbound_qty", sa.Integer(), server_default="0", nullable=False, comment="当日审核入库件数"),
        sa.Column("outbound_qty", sa.Integer(), server_default="0", nullable=False, comment="当日审核出库件数"),
        sa.Column("inbound_by_type", sa.JSON(), nullable=False, comment="入库按类型件数"),
        sa.Column("outbound_by_type", sa.JSON(), nullable=False, comment="出库按类型件数"),
        sa.Column("closing_in_stock_qty", sa.Integer(), nullable=False, comment="期末在库件数"),
        sa.Column("closing_asset_amount", sa.Numeric(precision=14, scale=2), nullable=True, comment="期末在库资产金额"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sku_id"], ["product_sku.id"]),
        sa.PrimaryKeyConstraint("snapshot_date", "sku_id"),
    )


def downgrade():
    op.drop_table("inventory_sku_daily_ledger")
