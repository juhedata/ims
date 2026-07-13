"""add unit_price to inventory_item

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-14 11:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_item",
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=True, comment="采购单价"),
    )


def downgrade():
    op.drop_column("inventory_item", "unit_price")
