"""add customer weight column

Revision ID: k5l6m7n8o9p0
Revises: j4k5l6m7n8o9
Create Date: 2026-06-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "k5l6m7n8o9p0"
down_revision = "j4k5l6m7n8o9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "customer",
        sa.Column("weight", sa.Integer(), nullable=False, server_default="0", comment="权重，越高越靠前"),
    )


def downgrade():
    op.drop_column("customer", "weight")
