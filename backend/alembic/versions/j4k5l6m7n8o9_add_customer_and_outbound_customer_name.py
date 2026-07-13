"""add customer table and outbound customer_name

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-06-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "j4k5l6m7n8o9"
down_revision = "i3j4k5l6m7n8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="客户ID"),
        sa.Column("name", sa.String(length=200), nullable=False, comment="客户名称"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.add_column(
        "outbound_order",
        sa.Column("customer_name", sa.String(length=200), nullable=True, comment="客户名称"),
    )


def downgrade():
    op.drop_column("outbound_order", "customer_name")
    op.drop_table("customer")
