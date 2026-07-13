"""add unit_price to inbound_order_line

Revision ID: b1c2d3e4f5a6
Revises: f8a2b3c4d5e6
Create Date: 2026-06-14 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "f8a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inbound_order_line",
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=True, comment="采购单价"),
    )


def downgrade():
    op.drop_column("inbound_order_line", "unit_price")
