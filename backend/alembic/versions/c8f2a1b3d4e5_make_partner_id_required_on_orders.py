"""make partner_id required on inbound/outbound orders

Revision ID: c8f2a1b3d4e5
Revises: a43f9ddeab1a
Create Date: 2026-06-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c8f2a1b3d4e5"
down_revision = "a43f9ddeab1a"
branch_labels = None
depends_on = None


def _ensure_default_partner(conn) -> int:
    """为历史空单据回填 partner_id：优先用已有启用单位，否则创建占位单位。"""
    partner_id = conn.execute(
        sa.text("SELECT id FROM partner WHERE status = 1 ORDER BY id LIMIT 1")
    ).scalar()
    if partner_id is not None:
        return partner_id

    group_id = conn.execute(
        sa.text("SELECT id FROM partner_group ORDER BY id LIMIT 1")
    ).scalar()
    if group_id is None:
        conn.execute(sa.text("INSERT INTO partner_group (name) VALUES ('默认分组')"))
        group_id = conn.execute(
            sa.text("SELECT id FROM partner_group ORDER BY id DESC LIMIT 1")
        ).scalar()

    conn.execute(
        sa.text(
            "INSERT INTO partner (name, group_id, partner_type, status) "
            "VALUES ('未指定（历史数据）', :group_id, 0, 1)"
        ),
        {"group_id": group_id},
    )
    return conn.execute(
        sa.text("SELECT id FROM partner ORDER BY id DESC LIMIT 1")
    ).scalar()


def upgrade():
    conn = op.get_bind()
    default_partner_id = _ensure_default_partner(conn)

    conn.execute(
        sa.text("UPDATE inbound_order SET partner_id = :pid WHERE partner_id IS NULL"),
        {"pid": default_partner_id},
    )
    conn.execute(
        sa.text("UPDATE outbound_order SET partner_id = :pid WHERE partner_id IS NULL"),
        {"pid": default_partner_id},
    )

    op.drop_constraint("inbound_order_ibfk_1", "inbound_order", type_="foreignkey")
    op.drop_constraint("outbound_order_ibfk_1", "outbound_order", type_="foreignkey")

    op.alter_column(
        "inbound_order",
        "partner_id",
        existing_type=sa.Integer(),
        nullable=False,
        existing_comment="往来单位",
    )
    op.alter_column(
        "outbound_order",
        "partner_id",
        existing_type=sa.Integer(),
        nullable=False,
        existing_comment="往来单位",
    )

    op.create_foreign_key(
        "inbound_order_ibfk_1", "inbound_order", "partner", ["partner_id"], ["id"]
    )
    op.create_foreign_key(
        "outbound_order_ibfk_1", "outbound_order", "partner", ["partner_id"], ["id"]
    )


def downgrade():
    op.drop_constraint("inbound_order_ibfk_1", "inbound_order", type_="foreignkey")
    op.drop_constraint("outbound_order_ibfk_1", "outbound_order", type_="foreignkey")

    op.alter_column(
        "outbound_order",
        "partner_id",
        existing_type=sa.Integer(),
        nullable=True,
        existing_comment="往来单位",
    )
    op.alter_column(
        "inbound_order",
        "partner_id",
        existing_type=sa.Integer(),
        nullable=True,
        existing_comment="往来单位",
    )

    op.create_foreign_key(
        "outbound_order_ibfk_1", "outbound_order", "partner", ["partner_id"], ["id"]
    )
    op.create_foreign_key(
        "inbound_order_ibfk_1", "inbound_order", "partner", ["partner_id"], ["id"]
    )
