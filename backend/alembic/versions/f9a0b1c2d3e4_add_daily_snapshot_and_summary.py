"""add daily snapshot fields and inventory_daily_summary table

Revision ID: f9a0b1c2d3e4
Revises: e4f5a6b7c8d9
Create Date: 2026-06-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f9a0b1c2d3e4"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_item_snapshot",
        sa.Column("snapshot_date", sa.Date(), nullable=True, comment="快照业务日期"),
    )
    op.add_column(
        "inventory_item_snapshot",
        sa.Column(
            "snapshot_type",
            sa.String(length=10),
            server_default="MONTHLY",
            nullable=False,
            comment="DAILY/MONTHLY",
        ),
    )
    op.create_index(
        op.f("ix_inventory_item_snapshot_snapshot_date"),
        "inventory_item_snapshot",
        ["snapshot_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_item_snapshot_snapshot_type"),
        "inventory_item_snapshot",
        ["snapshot_type"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_item_snapshot_date_type",
        "inventory_item_snapshot",
        ["snapshot_date", "snapshot_type"],
        unique=False,
    )

    # 历史数据回填：按 snapshot_at 推导业务日期，标记为 MONTHLY
    op.execute(
        """
        UPDATE inventory_item_snapshot
        SET snapshot_date = DATE(snapshot_at),
            snapshot_type = 'MONTHLY'
        WHERE snapshot_date IS NULL
        """
    )

    op.create_table(
        "inventory_daily_summary",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False, comment="业务日期"),
        sa.Column("opening_in_stock_qty", sa.Integer(), nullable=True, comment="期初在库件数"),
        sa.Column("inbound_qty", sa.Integer(), server_default="0", nullable=False, comment="当日审核入库件数"),
        sa.Column("outbound_qty", sa.Integer(), server_default="0", nullable=False, comment="当日审核出库件数"),
        sa.Column("closing_in_stock_qty", sa.Integer(), nullable=False, comment="期末在库件数"),
        sa.Column("closing_asset_amount", sa.Numeric(precision=14, scale=2), nullable=True, comment="期末在库资产金额"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_date"),
    )
    op.create_index(
        op.f("ix_inventory_daily_summary_snapshot_date"),
        "inventory_daily_summary",
        ["snapshot_date"],
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix_inventory_daily_summary_snapshot_date"), table_name="inventory_daily_summary")
    op.drop_table("inventory_daily_summary")
    op.drop_index("ix_inventory_item_snapshot_date_type", table_name="inventory_item_snapshot")
    op.drop_index(op.f("ix_inventory_item_snapshot_snapshot_type"), table_name="inventory_item_snapshot")
    op.drop_index(op.f("ix_inventory_item_snapshot_snapshot_date"), table_name="inventory_item_snapshot")
    op.drop_column("inventory_item_snapshot", "snapshot_type")
    op.drop_column("inventory_item_snapshot", "snapshot_date")
