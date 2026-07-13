"""add sys_audit_log table

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-06-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sys_audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=True, comment="操作人 ID"),
        sa.Column("operator_name", sa.String(length=100), nullable=False, comment="操作人账号/昵称快照"),
        sa.Column("action", sa.String(length=30), nullable=False, comment="操作类型"),
        sa.Column("module", sa.String(length=30), nullable=False, comment="业务模块"),
        sa.Column("resource_type", sa.String(length=50), nullable=True, comment="资源类型"),
        sa.Column("resource_id", sa.String(length=100), nullable=True, comment="资源标识"),
        sa.Column("resource_name", sa.String(length=200), nullable=True, comment="资源名称/单号"),
        sa.Column("summary", sa.String(length=500), nullable=False, comment="操作摘要"),
        sa.Column("before_data", sa.Text(), nullable=True, comment="变更前数据 JSON"),
        sa.Column("after_data", sa.Text(), nullable=True, comment="变更后数据 JSON"),
        sa.Column("ip_address", sa.String(length=45), nullable=True, comment="客户端 IP"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="操作时间"),
        sa.ForeignKeyConstraint(["operator_id"], ["sys_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sys_audit_log_action"), "sys_audit_log", ["action"], unique=False)
    op.create_index(op.f("ix_sys_audit_log_created_at"), "sys_audit_log", ["created_at"], unique=False)
    op.create_index(op.f("ix_sys_audit_log_module"), "sys_audit_log", ["module"], unique=False)
    op.create_index(op.f("ix_sys_audit_log_operator_id"), "sys_audit_log", ["operator_id"], unique=False)
    op.create_index(op.f("ix_sys_audit_log_resource_id"), "sys_audit_log", ["resource_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_sys_audit_log_resource_id"), table_name="sys_audit_log")
    op.drop_index(op.f("ix_sys_audit_log_operator_id"), table_name="sys_audit_log")
    op.drop_index(op.f("ix_sys_audit_log_module"), table_name="sys_audit_log")
    op.drop_index(op.f("ix_sys_audit_log_created_at"), table_name="sys_audit_log")
    op.drop_index(op.f("ix_sys_audit_log_action"), table_name="sys_audit_log")
    op.drop_table("sys_audit_log")
