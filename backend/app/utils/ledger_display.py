"""库存流水/汇总页面展示分组（与前端 ledgerDisplay.js 一致）。"""
from app.models.enums import RETURN_CONDITION_ORDER, StockCondition

OTHER_INBOUND_TYPE_CODES = [c.value for c in RETURN_CONDITION_ORDER] + [
    StockCondition.RETURNED_FROM_BORROW.value,
]
OTHER_OUTBOUND_TYPE_CODES = ["SCRAPPED", "RND", "SAMPLE", "TRIAL", "REPAIR", "DEPT_PROCUREMENT", "BORROWED"]

LEDGER_INBOUND_DISPLAY_HEADERS = ["入库-正常", "入库-其他入库"]
LEDGER_OUTBOUND_DISPLAY_HEADERS = [
    "出库-售出-线上",
    "出库-售出-线下",
    "出库-准售出",
    "出库-赠送",
    "出库-其他出库",
]


def _sum_type_qty(type_qty: dict[str, int] | None, codes: list[str]) -> int:
    type_qty = type_qty or {}
    return sum(int(type_qty.get(code, 0)) for code in codes)


def inbound_display_values(inbound_by_type: dict[str, int] | None) -> list[int]:
    """入库展示列：正常、其他入库。"""
    inbound_by_type = inbound_by_type or {}
    normal = int(inbound_by_type.get(StockCondition.NEW.value, 0))
    other = _sum_type_qty(inbound_by_type, OTHER_INBOUND_TYPE_CODES)
    return [normal, other]


def outbound_display_values(outbound_by_type: dict[str, int] | None) -> list[int]:
    """出库展示列：售出-线上、售出-线下、准售出、赠送、其他出库。"""
    outbound_by_type = outbound_by_type or {}
    other = _sum_type_qty(outbound_by_type, OTHER_OUTBOUND_TYPE_CODES)
    return [
        int(outbound_by_type.get("SOLD", 0)),
        int(outbound_by_type.get("SOLD_OFFLINE", 0)),
        int(outbound_by_type.get("PRESOLD", 0)),
        int(outbound_by_type.get("GIFTED", 0)),
        other,
    ]
