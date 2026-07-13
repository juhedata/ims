"""SKU 日流水表：入库/出库类型与列名映射。"""
from app.models.enums import (
    OutboundType,
    RETURN_CONDITION_ORDER,
    StockCondition,
)

# 入库类型 code 列表（与前端 IN_STOCK_CONDITION_ORDER 一致）
LEDGER_INBOUND_TYPE_CODES = [StockCondition.NEW.value] + [c.value for c in RETURN_CONDITION_ORDER]

# 出库类型 code 列表（含 BORROWED）
LEDGER_OUTBOUND_TYPE_CODES = [t.value for t in OutboundType]


def inbound_type_column(type_code: str) -> str:
    """入库类型 code → 表字段名。"""
    return f"inbound_{type_code.lower()}"


def outbound_type_column(type_code: str) -> str:
    """出库类型 code → 表字段名。"""
    return f"outbound_{type_code.lower()}"


INBOUND_TYPE_COLUMNS: dict[str, str] = {
    code: inbound_type_column(code) for code in LEDGER_INBOUND_TYPE_CODES
}
OUTBOUND_TYPE_COLUMNS: dict[str, str] = {
    code: outbound_type_column(code) for code in LEDGER_OUTBOUND_TYPE_CODES
}


def inbound_type_values(type_qty: dict[str, int] | None) -> dict[str, int]:
    """入库类型数量 dict → ORM 字段 kwargs。"""
    type_qty = type_qty or {}
    return {col: int(type_qty.get(code, 0)) for code, col in INBOUND_TYPE_COLUMNS.items()}


def outbound_type_values(type_qty: dict[str, int] | None) -> dict[str, int]:
    """出库类型数量 dict → ORM 字段 kwargs。"""
    type_qty = type_qty or {}
    return {col: int(type_qty.get(code, 0)) for code, col in OUTBOUND_TYPE_COLUMNS.items()}


def read_inbound_by_type(row) -> dict[str, int]:
    """ORM 行 → 入库类型数量 dict（供 API / 导出）。"""
    return {code: getattr(row, col, 0) or 0 for code, col in INBOUND_TYPE_COLUMNS.items()}


def read_outbound_by_type(row) -> dict[str, int]:
    """ORM 行 → 出库类型数量 dict（供 API / 导出）。"""
    return {code: getattr(row, col, 0) or 0 for code, col in OUTBOUND_TYPE_COLUMNS.items()}
