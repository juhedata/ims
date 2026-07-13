"""add rnd sample trial outbound types and stock enums

Revision ID: e7f1a2b3c4d5
Revises: da1389b468cc
Create Date: 2026-06-10 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e7f1a2b3c4d5"
down_revision = "da1389b468cc"
branch_labels = None
depends_on = None


NEW_ENUMS = [
    ("stock_status", "RND", "研发", 6),
    ("stock_status", "SAMPLE", "样机", 7),
    ("stock_status", "TRIAL", "试用", 8),
    ("stock_condition", "RETURNED_FROM_RND", "研发退回", 5),
    ("stock_condition", "RETURNED_FROM_SAMPLE", "样机退回", 6),
    ("stock_condition", "RETURNED_FROM_TRIAL", "试用退回", 7),
    ("outbound_type", "RND", "研发", 5),
    ("outbound_type", "SAMPLE", "样机", 6),
    ("outbound_type", "TRIAL", "试用", 7),
    ("inbound_type", "RETURNED_FROM_RND", "研发退回", 5),
    ("inbound_type", "RETURNED_FROM_SAMPLE", "样机退回", 6),
    ("inbound_type", "RETURNED_FROM_TRIAL", "试用退回", 7),
]


def _insert_enums(conn) -> None:
    for category, code, label, sort_order in NEW_ENUMS:
        exists = conn.execute(
            sa.text(
                "SELECT id FROM sys_enum WHERE category = :category AND code = :code LIMIT 1"
            ),
            {"category": category, "code": code},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO sys_enum (category, code, label, sort_order, enabled) "
                "VALUES (:category, :code, :label, :sort_order, 1)"
            ),
            {
                "category": category,
                "code": code,
                "label": label,
                "sort_order": sort_order,
            },
        )


def _delete_enums(conn) -> None:
    for category, code, _, _ in NEW_ENUMS:
        conn.execute(
            sa.text("DELETE FROM sys_enum WHERE category = :category AND code = :code"),
            {"category": category, "code": code},
        )


def upgrade():
    conn = op.get_bind()
    _insert_enums(conn)


def downgrade():
    conn = op.get_bind()
    _delete_enums(conn)
