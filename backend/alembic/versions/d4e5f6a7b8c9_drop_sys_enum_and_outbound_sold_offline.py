"""drop sys_enum and migrate outbound sold offline type

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-22 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE outbound_order SET outbound_type = 'SOLD_OFFLINE' "
            "WHERE outbound_type IN ('PRESOLD', 'OFFLINE_SOLD')"
        )
    )
    # 表可能已被手动删除；MySQL 不支持 DROP INDEX IF EXISTS，直接删表即可
    conn.execute(sa.text("DROP TABLE IF EXISTS sys_enum"))


def downgrade():
    op.create_table(
        "sys_enum",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, comment="枚举分类"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="枚举代码"),
        sa.Column("label", sa.String(length=100), nullable=False, comment="展示名称"),
        sa.Column("sort_order", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("enabled", sa.SmallInteger(), nullable=False, comment="1=启用 0=禁用"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "code", name="uk_enum_category_code"),
    )
    op.create_index(op.f("ix_sys_enum_category"), "sys_enum", ["category"], unique=False)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE outbound_order SET outbound_type = 'PRESOLD' "
            "WHERE outbound_type = 'SOLD_OFFLINE'"
        )
    )
