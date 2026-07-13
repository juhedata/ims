"""split sku daily ledger json type columns into individual columns

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-06-23 16:00:00.000000

"""
import json

from alembic import op
import sqlalchemy as sa


revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None

INBOUND_COLUMNS = {
    "NEW": "inbound_new",
    "RETURNED_FROM_SALE": "inbound_returned_from_sale",
    "RETURNED_FROM_SOLD_OFFLINE": "inbound_returned_from_sold_offline",
    "RETURNED_FROM_PRESOLD": "inbound_returned_from_presold",
    "RETURNED_FROM_GIFT": "inbound_returned_from_gift",
    "RETURNED_FROM_SCRAPPED": "inbound_returned_from_scrapped",
    "RETURNED_FROM_RND": "inbound_returned_from_rnd",
    "RETURNED_FROM_SAMPLE": "inbound_returned_from_sample",
    "RETURNED_FROM_TRIAL": "inbound_returned_from_trial",
    "RETURNED_FROM_REPAIR": "inbound_returned_from_repair",
}

OUTBOUND_COLUMNS = {
    "SOLD": "outbound_sold",
    "SOLD_OFFLINE": "outbound_sold_offline",
    "OFFLINE_SOLD": "outbound_sold_offline",
    "PRESOLD": "outbound_presold",
    "GIFTED": "outbound_gifted",
    "SCRAPPED": "outbound_scrapped",
    "RND": "outbound_rnd",
    "SAMPLE": "outbound_sample",
    "TRIAL": "outbound_trial",
    "REPAIR": "outbound_repair",
    "BORROWED": "outbound_borrowed",
}


def _add_type_columns() -> None:
    for column in INBOUND_COLUMNS.values():
        op.add_column(
            "inventory_sku_daily_ledger",
            sa.Column(column, sa.Integer(), server_default="0", nullable=False),
        )
    for column in set(OUTBOUND_COLUMNS.values()):
        op.add_column(
            "inventory_sku_daily_ledger",
            sa.Column(column, sa.Integer(), server_default="0", nullable=False),
        )


def _migrate_json_data() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT snapshot_date, sku_id, inbound_by_type, outbound_by_type "
            "FROM inventory_sku_daily_ledger"
        )
    ).fetchall()
    for snapshot_date, sku_id, inbound_json, outbound_json in rows:
        inbound_data = inbound_json if isinstance(inbound_json, dict) else json.loads(inbound_json or "{}")
        outbound_data = outbound_json if isinstance(outbound_json, dict) else json.loads(outbound_json or "{}")
        set_parts: list[str] = []
        params: dict = {"snapshot_date": snapshot_date, "sku_id": sku_id}
        for code, column in INBOUND_COLUMNS.items():
            set_parts.append(f"{column} = :{column}")
            params[column] = int(inbound_data.get(code, 0))
        outbound_totals: dict[str, int] = {}
        for code, qty in outbound_data.items():
            column = OUTBOUND_COLUMNS.get(code)
            if not column:
                continue
            outbound_totals[column] = outbound_totals.get(column, 0) + int(qty or 0)
        for column in set(OUTBOUND_COLUMNS.values()):
            set_parts.append(f"{column} = :{column}")
            params[column] = outbound_totals.get(column, 0)
        bind.execute(
            sa.text(
                "UPDATE inventory_sku_daily_ledger SET "
                + ", ".join(set_parts)
                + " WHERE snapshot_date = :snapshot_date AND sku_id = :sku_id"
            ),
            params,
        )


def upgrade():
    _add_type_columns()
    _migrate_json_data()
    op.drop_column("inventory_sku_daily_ledger", "inbound_by_type")
    op.drop_column("inventory_sku_daily_ledger", "outbound_by_type")


def downgrade():
    op.add_column(
        "inventory_sku_daily_ledger",
        sa.Column("inbound_by_type", sa.JSON(), nullable=False),
    )
    op.add_column(
        "inventory_sku_daily_ledger",
        sa.Column("outbound_by_type", sa.JSON(), nullable=False),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT snapshot_date, sku_id, "
            + ", ".join(INBOUND_COLUMNS.values())
            + ", "
            + ", ".join(sorted(set(OUTBOUND_COLUMNS.values())))
            + " FROM inventory_sku_daily_ledger"
        )
    ).mappings().all()

    reverse_inbound = {col: code for code, col in INBOUND_COLUMNS.items()}
    reverse_outbound = {
        "outbound_sold": "SOLD",
        "outbound_sold_offline": "SOLD_OFFLINE",
        "outbound_presold": "PRESOLD",
        "outbound_gifted": "GIFTED",
        "outbound_scrapped": "SCRAPPED",
        "outbound_rnd": "RND",
        "outbound_sample": "SAMPLE",
        "outbound_trial": "TRIAL",
        "outbound_repair": "REPAIR",
        "outbound_borrowed": "BORROWED",
    }

    for row in rows:
        inbound_json = {reverse_inbound[col]: int(row[col]) for col in INBOUND_COLUMNS.values()}
        outbound_json = {
            code: int(row[col]) for col, code in reverse_outbound.items() if int(row[col]) > 0
        }
        bind.execute(
            sa.text(
                "UPDATE inventory_sku_daily_ledger "
                "SET inbound_by_type = :inbound_by_type, outbound_by_type = :outbound_by_type "
                "WHERE snapshot_date = :snapshot_date AND sku_id = :sku_id"
            ),
            {
                "snapshot_date": row["snapshot_date"],
                "sku_id": row["sku_id"],
                "inbound_by_type": json.dumps(inbound_json, ensure_ascii=False),
                "outbound_by_type": json.dumps(outbound_json, ensure_ascii=False),
            },
        )

    for column in reversed(list(INBOUND_COLUMNS.values()) + sorted(set(OUTBOUND_COLUMNS.values()))):
        op.drop_column("inventory_sku_daily_ledger", column)
