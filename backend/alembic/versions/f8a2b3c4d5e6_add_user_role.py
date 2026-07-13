"""add user role column

Revision ID: f8a2b3c4d5e6
Revises: e7f1a2b3c4d5
Create Date: 2026-06-10 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f8a2b3c4d5e6"
down_revision = "e7f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sys_user",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="STAFF", comment="角色：ADMIN/STAFF"),
    )
    op.execute("UPDATE sys_user SET role = 'ADMIN' WHERE username = 'admin'")


def downgrade() -> None:
    op.drop_column("sys_user", "role")
