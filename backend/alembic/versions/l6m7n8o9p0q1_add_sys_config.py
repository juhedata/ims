"""add sys_config table

Revision ID: l6m7n8o9p0q1
Revises: k5l6m7n8o9p0
Create Date: 2026-07-10 13:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "l6m7n8o9p0q1"
down_revision = "k5l6m7n8o9p0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sys_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("key", sa.String(length=64), nullable=False, comment="配置键"),
        sa.Column("value", sa.Text(), nullable=True, comment="配置值"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_sys_config_key", "sys_config", ["key"], unique=False)

    # 写入开源默认品牌配置
    op.execute(
        "INSERT INTO sys_config (`key`, `value`) VALUES "
        "('app_name', 'IMS'), "
        "('app_subtitle', '一物一码库存管理系统')"
    )


def downgrade():
    op.drop_index("ix_sys_config_key", table_name="sys_config")
    op.drop_table("sys_config")
