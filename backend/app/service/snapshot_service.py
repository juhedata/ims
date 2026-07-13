from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.constants.sku_daily_ledger import (
    LEDGER_INBOUND_TYPE_CODES,
    LEDGER_OUTBOUND_TYPE_CODES,
    inbound_type_values,
    outbound_type_values,
    read_inbound_by_type,
    read_outbound_by_type,
)
from app.models.enums import (
    OperationStatus,
    OutboundType,
    StockStatus,
)
from app.models.inbound import InboundOrder, InboundOrderLine
from app.models.inventory import InventoryDailySummary, InventoryItem, InventoryItemSnapshot, InventorySkuDailyLedger
from app.models.outbound import OutboundOrder, OutboundOrderItem
from app.models.product import ProductSku
from app.utils.item_export import _IN_STOCK_CONDITION_LABELS
from app.service.inventory_service import _attach_order_remark, _attach_partner_info
from app.utils.item_export import build_items_xlsx, build_ledger_xlsx, build_ledger_summary_xlsx

SNAPSHOT_TYPE_DAILY = "DAILY"

# 流水/汇总中入库、出库类型列顺序（与 sku_daily_ledger 表字段一致）
LEDGER_INBOUND_TYPES = LEDGER_INBOUND_TYPE_CODES
LEDGER_OUTBOUND_TYPES = LEDGER_OUTBOUND_TYPE_CODES


def _normalize_outbound_type_key(outbound_type: str) -> str:
    """归一化出库类型 code（兼容历史 OFFLINE_SOLD）。"""
    if outbound_type == "OFFLINE_SOLD":
        return OutboundType.SOLD_OFFLINE.value
    return outbound_type


def _merge_qty_dicts(base: dict[str, int], addition: dict[str, int]) -> dict[str, int]:
    """累加数量字典。"""
    for key, qty in addition.items():
        base[key] = base.get(key, 0) + qty
    return base


def create_snapshot(
    db: Session,
    snapshot_at: datetime | None = None,
    replace_existing: bool = True,
) -> dict:
    """对 inventory_item 全量日快照，并同步生成日汇总。"""
    snapshot_at = snapshot_at or datetime.now()
    snapshot_date = snapshot_at.date()
    snapshot_month = snapshot_at.strftime("%Y-%m")

    if replace_existing:
        _clear_daily_snapshot(db, snapshot_date)

    items = db.query(InventoryItem).all()
    count = 0
    for item in items:
        snap = InventoryItemSnapshot(
            snapshot_at=snapshot_at,
            snapshot_date=snapshot_date,
            snapshot_type=SNAPSHOT_TYPE_DAILY,
            snapshot_month=snapshot_month,
            item_id=item.id,
            item_sn=item.item_sn,
            sku_id=item.sku_id,
            stock_status=item.stock_status,
            stock_condition=item.stock_condition,
            operation_status=item.operation_status,
            last_order_no=item.last_order_no,
            unit_price=item.unit_price,
            quantity=item.quantity,
        )
        db.add(snap)
        count += 1

    # SessionLocal 关闭 autoflush，SKU 流水依赖快照明细查询，须先 flush
    db.flush()

    build_daily_summary(db, snapshot_date, items)
    build_sku_daily_ledger(db, snapshot_date)
    db.commit()
    return {
        "snapshot_at": snapshot_at,
        "snapshot_date": snapshot_date.isoformat(),
        "snapshot_type": SNAPSHOT_TYPE_DAILY,
        "item_count": count,
    }


def create_daily_snapshot(db: Session, snapshot_at: datetime | None = None) -> dict:
    """创建日快照（幂等：同日覆盖）。"""
    return create_snapshot(db, snapshot_at, replace_existing=True)


def _is_in_stock_asset(stock_status: str, operation_status: str) -> bool:
    """在库资产口径：在库且操作已完成。"""
    return (
        stock_status == StockStatus.IN_STOCK.value
        and operation_status == OperationStatus.COMPLETED.value
    )


def _count_in_stock(items) -> tuple[int, Decimal]:
    """统计在库件数与资产金额。"""
    qty = 0
    amount = Decimal("0")
    for item in items:
        if _is_in_stock_asset(item.stock_status, item.operation_status):
            piece = item.quantity or 1
            qty += piece
            if item.unit_price is not None:
                amount += Decimal(str(item.unit_price)) * piece
    return qty, amount


def _clear_daily_snapshot(db: Session, snapshot_date: date) -> None:
    """删除某日已有日快照及汇总，便于幂等重跑。"""
    db.query(InventoryItemSnapshot).filter(
        InventoryItemSnapshot.snapshot_date == snapshot_date,
        InventoryItemSnapshot.snapshot_type == SNAPSHOT_TYPE_DAILY,
    ).delete(synchronize_session=False)
    db.query(InventoryDailySummary).filter(
        InventoryDailySummary.snapshot_date == snapshot_date,
    ).delete(synchronize_session=False)
    db.query(InventorySkuDailyLedger).filter(
        InventorySkuDailyLedger.snapshot_date == snapshot_date,
    ).delete(synchronize_session=False)


def _day_order_qty(db: Session, snapshot_date: date) -> tuple[int, int]:
    """统计某日审核通过的入库/出库件数。"""
    day_start = datetime.combine(snapshot_date, time.min)
    day_end = datetime.combine(snapshot_date, time.max)
    inbound_qty = (
        db.query(func.coalesce(func.sum(InboundOrder.total_qty), 0))
        .filter(
            InboundOrder.operation_status == OperationStatus.COMPLETED.value,
            InboundOrder.reviewed_at >= day_start,
            InboundOrder.reviewed_at <= day_end,
        )
        .scalar()
    )
    outbound_qty = (
        db.query(func.coalesce(func.sum(OutboundOrder.total_qty), 0))
        .filter(
            OutboundOrder.operation_status == OperationStatus.COMPLETED.value,
            OutboundOrder.reviewed_at >= day_start,
            OutboundOrder.reviewed_at <= day_end,
        )
        .scalar()
    )
    return int(inbound_qty or 0), int(outbound_qty or 0)


def build_daily_summary(db: Session, snapshot_date: date, items: list[InventoryItem] | None = None) -> InventoryDailySummary:
    """根据日快照写入/更新日汇总。"""
    if items is None:
        snaps = (
            db.query(InventoryItemSnapshot)
            .filter(
                InventoryItemSnapshot.snapshot_date == snapshot_date,
                InventoryItemSnapshot.snapshot_type == SNAPSHOT_TYPE_DAILY,
            )
            .all()
        )
        closing_qty, closing_amount = _count_in_stock(snaps)
    else:
        closing_qty, closing_amount = _count_in_stock(items)

    inbound_qty, outbound_qty = _day_order_qty(db, snapshot_date)
    prev = (
        db.query(InventoryDailySummary)
        .filter(InventoryDailySummary.snapshot_date < snapshot_date)
        .order_by(InventoryDailySummary.snapshot_date.desc())
        .first()
    )
    opening_qty = prev.closing_in_stock_qty if prev else None

    summary = (
        db.query(InventoryDailySummary)
        .filter(InventoryDailySummary.snapshot_date == snapshot_date)
        .first()
    )
    if summary:
        summary.opening_in_stock_qty = opening_qty
        summary.inbound_qty = inbound_qty
        summary.outbound_qty = outbound_qty
        summary.closing_in_stock_qty = closing_qty
        summary.closing_asset_amount = closing_amount
    else:
        summary = InventoryDailySummary(
            snapshot_date=snapshot_date,
            opening_in_stock_qty=opening_qty,
            inbound_qty=inbound_qty,
            outbound_qty=outbound_qty,
            closing_in_stock_qty=closing_qty,
            closing_asset_amount=closing_amount,
        )
        db.add(summary)
    return summary


def _compute_sku_daily_ledger_rows(db: Session, snapshot_date: date) -> list[dict]:
    """计算某日各 SKU 库存流水（快照任务写入前调用）。"""
    rows: list[dict] = []
    for item in get_daily_ledger_breakdown(db, snapshot_date, "sku"):
        sku_id = int(item["dimension_key"])
        inbound_by_type = _day_inbound_by_condition_for_sku(db, snapshot_date, sku_id)
        outbound_by_type = _day_outbound_by_type_for_sku(db, snapshot_date, sku_id)
        rows.append({
            "sku_id": sku_id,
            "sku_name": item["dimension_label"],
            "opening_in_stock_qty": item["opening_in_stock_qty"],
            "inbound_qty": item["inbound_qty"],
            "outbound_qty": item["outbound_qty"],
            "inbound_by_type": inbound_by_type,
            "outbound_by_type": outbound_by_type,
            "closing_in_stock_qty": item["closing_in_stock_qty"],
            "closing_asset_amount": item["closing_asset_amount"],
        })
    return rows


def build_sku_daily_ledger(db: Session, snapshot_date: date) -> int:
    """写入某日 SKU 日流水（调用前需已清除同日旧数据）。"""
    rows = _compute_sku_daily_ledger_rows(db, snapshot_date)
    for row in rows:
        db.add(InventorySkuDailyLedger(
            snapshot_date=snapshot_date,
            sku_id=row["sku_id"],
            opening_in_stock_qty=row["opening_in_stock_qty"],
            inbound_qty=row["inbound_qty"],
            outbound_qty=row["outbound_qty"],
            closing_in_stock_qty=row["closing_in_stock_qty"],
            closing_asset_amount=row["closing_asset_amount"],
            **inbound_type_values(row["inbound_by_type"]),
            **outbound_type_values(row["outbound_by_type"]),
        ))
    return len(rows)


def _sku_daily_ledger_to_dict(row: InventorySkuDailyLedger, sku_name: str | None = None) -> dict:
    """将 SKU 日流水 ORM 行转为 API 字典。"""
    return {
        "snapshot_date": row.snapshot_date.isoformat(),
        "sku_id": row.sku_id,
        "sku_name": sku_name,
        "opening_in_stock_qty": row.opening_in_stock_qty,
        "inbound_qty": row.inbound_qty,
        "outbound_qty": row.outbound_qty,
        "inbound_by_type": read_inbound_by_type(row),
        "outbound_by_type": read_outbound_by_type(row),
        "closing_in_stock_qty": row.closing_in_stock_qty,
        "closing_asset_amount": row.closing_asset_amount,
    }


def list_snapshots(db: Session) -> list[dict]:
    """列出所有快照批次（按时间分组）。"""
    rows = (
        db.query(
            InventoryItemSnapshot.snapshot_at,
            InventoryItemSnapshot.snapshot_type,
            func.count(InventoryItemSnapshot.id).label("item_count"),
        )
        .group_by(InventoryItemSnapshot.snapshot_at, InventoryItemSnapshot.snapshot_type)
        .order_by(InventoryItemSnapshot.snapshot_at.desc())
        .all()
    )
    return [{"snapshot_at": r[0], "snapshot_type": r[1], "item_count": r[2]} for r in rows]


def list_snapshot_dates(db: Session, date_from: date | None = None, date_to: date | None = None) -> list[str]:
    """列出存在日汇总的日期（YYYY-MM-DD，倒序）。"""
    query = db.query(InventoryDailySummary.snapshot_date)
    if date_from:
        query = query.filter(InventoryDailySummary.snapshot_date >= date_from)
    if date_to:
        query = query.filter(InventoryDailySummary.snapshot_date <= date_to)
    rows = query.order_by(InventoryDailySummary.snapshot_date.desc()).all()
    return [r[0].isoformat() for r in rows]


def get_daily_ledger(
    db: Session,
    date_from: date,
    date_to: date,
    sku_id: int | None = None,
) -> list[dict]:
    """查询日期区间内的库存日流水（从 inventory_sku_daily_ledger 读取）。"""
    query = (
        db.query(InventorySkuDailyLedger, ProductSku.name.label("sku_name"))
        .join(ProductSku, InventorySkuDailyLedger.sku_id == ProductSku.id)
        .filter(
            InventorySkuDailyLedger.snapshot_date >= date_from,
            InventorySkuDailyLedger.snapshot_date <= date_to,
        )
    )
    if sku_id is not None:
        query = query.filter(InventorySkuDailyLedger.sku_id == sku_id)
    query = query.order_by(
        InventorySkuDailyLedger.snapshot_date.desc(),
        ProductSku.name.asc(),
    )
    return [
        _sku_daily_ledger_to_dict(row, sku_name)
        for row, sku_name in query.all()
    ]


def get_daily_ledger_date_summary(
    db: Session,
    date_from: date,
    date_to: date,
) -> list[dict]:
    """查询日期区间内的库存日流水（按日期汇总，用于校验）。"""
    rows = (
        db.query(InventoryDailySummary)
        .filter(
            InventoryDailySummary.snapshot_date >= date_from,
            InventoryDailySummary.snapshot_date <= date_to,
        )
        .order_by(InventoryDailySummary.snapshot_date.asc())
        .all()
    )
    return [
        {
            "snapshot_date": row.snapshot_date.isoformat(),
            "opening_in_stock_qty": row.opening_in_stock_qty,
            "inbound_qty": row.inbound_qty,
            "outbound_qty": row.outbound_qty,
            "closing_in_stock_qty": row.closing_in_stock_qty,
            "closing_asset_amount": row.closing_asset_amount,
        }
        for row in rows
    ]


def export_daily_ledger_xlsx(
    db: Session, date_from: date, date_to: date, sku_id: int | None = None
) -> bytes:
    """导出库存日流水 Excel。"""
    rows = get_daily_ledger(db, date_from, date_to, sku_id=sku_id)
    return build_ledger_xlsx(rows)


def _dates_in_range(db: Session, date_from: date, date_to: date) -> list[date]:
    """返回区间内有日汇总的日期列表（升序）。"""
    rows = (
        db.query(InventoryDailySummary.snapshot_date)
        .filter(
            InventoryDailySummary.snapshot_date >= date_from,
            InventoryDailySummary.snapshot_date <= date_to,
        )
        .order_by(InventoryDailySummary.snapshot_date.asc())
        .all()
    )
    return [row[0] for row in rows]


def get_ledger_period_sku_summary(
    db: Session,
    date_from: date,
    date_to: date,
) -> list[dict]:
    """按 SKU 汇总日期区间内的库存流水。"""
    ledger_rows = get_daily_ledger(db, date_from, date_to)
    by_sku: dict[int, dict] = {}

    for row in ledger_rows:
        sku_id = row["sku_id"]
        snapshot_date = row["snapshot_date"]
        if sku_id not in by_sku:
            by_sku[sku_id] = {
                "sku_id": sku_id,
                "sku_name": row["sku_name"],
                "first_date": snapshot_date,
                "last_date": snapshot_date,
                "opening_in_stock_qty": row["opening_in_stock_qty"],
                "total_inbound_qty": row["inbound_qty"] or 0,
                "total_outbound_qty": row["outbound_qty"] or 0,
                "inbound_by_type": dict(row.get("inbound_by_type") or {}),
                "outbound_by_type": dict(row.get("outbound_by_type") or {}),
                "closing_in_stock_qty": row["closing_in_stock_qty"],
                "closing_asset_amount": row["closing_asset_amount"],
            }
        else:
            entry = by_sku[sku_id]
            if snapshot_date < entry["first_date"]:
                entry["first_date"] = snapshot_date
                entry["opening_in_stock_qty"] = row["opening_in_stock_qty"]
            if snapshot_date > entry["last_date"]:
                entry["last_date"] = snapshot_date
                entry["closing_in_stock_qty"] = row["closing_in_stock_qty"]
                entry["closing_asset_amount"] = row["closing_asset_amount"]
            entry["total_inbound_qty"] += row["inbound_qty"] or 0
            entry["total_outbound_qty"] += row["outbound_qty"] or 0
            _merge_qty_dicts(entry["inbound_by_type"], row.get("inbound_by_type") or {})
            _merge_qty_dicts(entry["outbound_by_type"], row.get("outbound_by_type") or {})

    items: list[dict] = []
    for entry in by_sku.values():
        opening = entry["opening_in_stock_qty"]
        expected = (
            opening + entry["total_inbound_qty"] - entry["total_outbound_qty"]
            if opening is not None
            else None
        )
        closing = entry["closing_in_stock_qty"]
        items.append({
            "sku_id": entry["sku_id"],
            "sku_name": entry["sku_name"],
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "opening_in_stock_qty": opening,
            "total_inbound_qty": entry["total_inbound_qty"],
            "total_outbound_qty": entry["total_outbound_qty"],
            "inbound_by_type": entry["inbound_by_type"],
            "outbound_by_type": entry["outbound_by_type"],
            "expected_closing_qty": expected,
            "closing_in_stock_qty": closing,
            "closing_asset_amount": entry["closing_asset_amount"],
            "balanced": expected is not None and expected == closing,
            "diff_qty": (closing - expected) if expected is not None else None,
        })
    return sorted(items, key=lambda item: item["sku_name"] or "")


def get_ledger_period_sku_condition_breakdown(
    db: Session,
    date_from: date,
    date_to: date,
    sku_id: int,
) -> list[dict]:
    """按库存属性汇总某 SKU 在日期区间内的库存流水。"""
    range_dates = _dates_in_range(db, date_from, date_to)
    if not range_dates:
        return []

    opening_items = {
        item["dimension_key"]: item
        for item in get_daily_ledger_sku_condition_breakdown(db, range_dates[0], sku_id)
    }
    closing_items = {
        item["dimension_key"]: item
        for item in get_daily_ledger_sku_condition_breakdown(db, range_dates[-1], sku_id)
    }
    inbound_totals: dict[str, int] = {}
    for snapshot_date in range_dates:
        for condition, qty in _day_inbound_by_condition_for_sku(db, snapshot_date, sku_id).items():
            inbound_totals[condition] = inbound_totals.get(condition, 0) + qty

    all_conditions = set(opening_items) | set(closing_items) | set(inbound_totals)
    items = []
    for condition in sorted(all_conditions, key=lambda c: _condition_label(c)):
        opening = opening_items.get(condition)
        closing = closing_items.get(condition)
        total_inbound = inbound_totals.get(condition, 0)
        opening_qty = opening["opening_in_stock_qty"] if opening else None
        closing_qty = closing["closing_in_stock_qty"] if closing else 0
        expected = opening_qty + total_inbound if opening_qty is not None else None
        items.append({
            "dimension_key": condition,
            "dimension_label": _condition_label(condition),
            "opening_in_stock_qty": opening_qty,
            "inbound_qty": total_inbound,
            "outbound_qty": 0,
            "closing_in_stock_qty": closing_qty,
            "closing_asset_amount": closing["closing_asset_amount"] if closing else None,
            "expected_closing_qty": expected,
            "balanced": expected is not None and expected == closing_qty,
            "diff_qty": (closing_qty - expected) if expected is not None else None,
        })
    return items


def export_ledger_period_sku_summary_xlsx(db: Session, date_from: date, date_to: date) -> bytes:
    """导出按 SKU 区间汇总 Excel。"""
    rows = get_ledger_period_sku_summary(db, date_from, date_to)
    return build_ledger_summary_xlsx(rows, date_from.isoformat(), date_to.isoformat())


def _prev_summary_date(db: Session, snapshot_date: date) -> date | None:
    """获取指定日期之前最近一个有汇总的日期。"""
    row = (
        db.query(InventoryDailySummary.snapshot_date)
        .filter(InventoryDailySummary.snapshot_date < snapshot_date)
        .order_by(InventoryDailySummary.snapshot_date.desc())
        .first()
    )
    return row[0] if row else None


def _all_product_skus(db: Session) -> dict[int, str]:
    """获取 product_sku 中启用状态的 SKU ID 与名称。"""
    rows = (
        db.query(ProductSku.id, ProductSku.name)
        .filter(ProductSku.status == 1)
        .order_by(ProductSku.name.asc())
        .all()
    )
    return {row.id: row.name for row in rows}


def _day_bounds(snapshot_date: date) -> tuple[datetime, datetime]:
    """返回某日审核时间范围的闭区间。"""
    return datetime.combine(snapshot_date, time.min), datetime.combine(snapshot_date, time.max)


def _in_stock_snapshots_query(db: Session, snapshot_date: date):
    """查询某日快照中在库且操作已完成的单品。"""
    return (
        db.query(InventoryItemSnapshot, ProductSku.name.label("sku_name"))
        .join(ProductSku, InventoryItemSnapshot.sku_id == ProductSku.id)
        .filter(
            InventoryItemSnapshot.snapshot_date == snapshot_date,
            InventoryItemSnapshot.snapshot_type == SNAPSHOT_TYPE_DAILY,
            InventoryItemSnapshot.stock_status == StockStatus.IN_STOCK.value,
            InventoryItemSnapshot.operation_status == OperationStatus.COMPLETED.value,
        )
    )


def _group_snapshots_by_sku(db: Session, snapshot_date: date) -> dict[int, dict]:
    """按 SKU 汇总某日快照在库件数与资产金额。"""
    result: dict[int, dict] = {}
    for snap, sku_name in _in_stock_snapshots_query(db, snapshot_date).all():
        entry = result.setdefault(
            snap.sku_id,
            {"sku_name": sku_name, "qty": 0, "amount": Decimal("0")},
        )
        piece = snap.quantity or 1
        entry["qty"] += piece
        if snap.unit_price is not None:
            entry["amount"] += Decimal(str(snap.unit_price)) * piece
    return result


def _group_snapshots_by_condition(db: Session, snapshot_date: date) -> dict[str, dict]:
    """按库存属性汇总某日快照在库件数与资产金额。"""
    result: dict[str, dict] = {}
    for snap, _ in _in_stock_snapshots_query(db, snapshot_date).all():
        entry = result.setdefault(
            snap.stock_condition,
            {"qty": 0, "amount": Decimal("0")},
        )
        piece = snap.quantity or 1
        entry["qty"] += piece
        if snap.unit_price is not None:
            entry["amount"] += Decimal(str(snap.unit_price)) * piece
    return result


def _day_inbound_by_sku(db: Session, snapshot_date: date) -> dict[int, dict]:
    """统计某日审核入库按 SKU 的件数。"""
    day_start, day_end = _day_bounds(snapshot_date)
    rows = (
        db.query(
            InboundOrderLine.sku_id,
            ProductSku.name,
            func.coalesce(func.sum(InboundOrderLine.quantity), 0),
        )
        .join(InboundOrder, InboundOrderLine.inbound_order_id == InboundOrder.id)
        .join(ProductSku, InboundOrderLine.sku_id == ProductSku.id)
        .filter(
            InboundOrder.operation_status == OperationStatus.COMPLETED.value,
            InboundOrder.reviewed_at >= day_start,
            InboundOrder.reviewed_at <= day_end,
        )
        .group_by(InboundOrderLine.sku_id, ProductSku.name)
        .all()
    )
    return {
        sku_id: {"sku_name": sku_name, "qty": int(qty or 0)}
        for sku_id, sku_name, qty in rows
    }


def _day_inbound_by_condition(db: Session, snapshot_date: date) -> dict[str, int]:
    """统计某日审核入库按库存属性的件数。"""
    day_start, day_end = _day_bounds(snapshot_date)
    rows = (
        db.query(
            InboundOrder.stock_condition,
            func.coalesce(func.sum(InboundOrder.total_qty), 0),
        )
        .filter(
            InboundOrder.operation_status == OperationStatus.COMPLETED.value,
            InboundOrder.reviewed_at >= day_start,
            InboundOrder.reviewed_at <= day_end,
        )
        .group_by(InboundOrder.stock_condition)
        .all()
    )
    return {condition: int(qty or 0) for condition, qty in rows}


def _day_outbound_by_sku(db: Session, snapshot_date: date) -> dict[int, dict]:
    """统计某日审核出库按 SKU 的件数。"""
    day_start, day_end = _day_bounds(snapshot_date)
    rows = (
        db.query(
            OutboundOrderItem.sku_id,
            ProductSku.name,
            func.count(OutboundOrderItem.id),
        )
        .join(OutboundOrder, OutboundOrderItem.outbound_order_id == OutboundOrder.id)
        .join(ProductSku, OutboundOrderItem.sku_id == ProductSku.id)
        .filter(
            OutboundOrder.operation_status == OperationStatus.COMPLETED.value,
            OutboundOrder.reviewed_at >= day_start,
            OutboundOrder.reviewed_at <= day_end,
        )
        .group_by(OutboundOrderItem.sku_id, ProductSku.name)
        .all()
    )
    return {
        sku_id: {"sku_name": sku_name, "qty": int(qty or 0)}
        for sku_id, sku_name, qty in rows
    }


def _condition_label(code: str) -> str:
    return _IN_STOCK_CONDITION_LABELS.get(code, code)


def _group_snapshots_by_condition_for_sku(db: Session, snapshot_date: date, sku_id: int) -> dict[str, dict]:
    """按库存属性汇总某日某 SKU 快照在库件数与资产金额。"""
    result: dict[str, dict] = {}
    query = _in_stock_snapshots_query(db, snapshot_date).filter(
        InventoryItemSnapshot.sku_id == sku_id,
    )
    for snap, _ in query.all():
        entry = result.setdefault(
            snap.stock_condition,
            {"qty": 0, "amount": Decimal("0")},
        )
        piece = snap.quantity or 1
        entry["qty"] += piece
        if snap.unit_price is not None:
            entry["amount"] += Decimal(str(snap.unit_price)) * piece
    return result


def _day_inbound_by_condition_for_sku(db: Session, snapshot_date: date, sku_id: int) -> dict[str, int]:
    """统计某日某 SKU 审核入库按库存属性的件数。"""
    day_start, day_end = _day_bounds(snapshot_date)
    rows = (
        db.query(
            InboundOrder.stock_condition,
            func.coalesce(func.sum(InboundOrderLine.quantity), 0),
        )
        .join(InboundOrder, InboundOrderLine.inbound_order_id == InboundOrder.id)
        .filter(
            InboundOrderLine.sku_id == sku_id,
            InboundOrder.operation_status == OperationStatus.COMPLETED.value,
            InboundOrder.reviewed_at >= day_start,
            InboundOrder.reviewed_at <= day_end,
        )
        .group_by(InboundOrder.stock_condition)
        .all()
    )
    return {condition: int(qty or 0) for condition, qty in rows}


def _day_outbound_by_type_for_sku(db: Session, snapshot_date: date, sku_id: int) -> dict[str, int]:
    """统计某日某 SKU 审核出库按出库类型的件数。"""
    day_start, day_end = _day_bounds(snapshot_date)
    rows = (
        db.query(
            OutboundOrder.outbound_type,
            func.count(OutboundOrderItem.id),
        )
        .join(OutboundOrder, OutboundOrderItem.outbound_order_id == OutboundOrder.id)
        .filter(
            OutboundOrderItem.sku_id == sku_id,
            OutboundOrder.operation_status == OperationStatus.COMPLETED.value,
            OutboundOrder.reviewed_at >= day_start,
            OutboundOrder.reviewed_at <= day_end,
        )
        .group_by(OutboundOrder.outbound_type)
        .all()
    )
    result: dict[str, int] = {}
    for outbound_type, qty in rows:
        key = _normalize_outbound_type_key(outbound_type)
        result[key] = result.get(key, 0) + int(qty or 0)
    return result


def get_daily_ledger_sku_condition_breakdown(
    db: Session,
    snapshot_date: date,
    sku_id: int,
) -> list[dict]:
    """按库存属性汇总某日某 SKU 的库存流水明细。"""
    prev_date = _prev_summary_date(db, snapshot_date)
    opening_by_condition = (
        _group_snapshots_by_condition_for_sku(db, prev_date, sku_id) if prev_date else {}
    )
    closing_by_condition = _group_snapshots_by_condition_for_sku(db, snapshot_date, sku_id)
    inbound_by_condition = _day_inbound_by_condition_for_sku(db, snapshot_date, sku_id)

    all_conditions = set(opening_by_condition) | set(closing_by_condition) | set(inbound_by_condition)
    items = []
    for condition in sorted(all_conditions, key=lambda c: _condition_label(c)):
        opening = opening_by_condition.get(condition)
        closing = closing_by_condition.get(condition)
        items.append({
            "dimension_key": condition,
            "dimension_label": _condition_label(condition),
            "opening_in_stock_qty": opening["qty"] if opening else (None if prev_date is None else 0),
            "inbound_qty": inbound_by_condition.get(condition, 0),
            "outbound_qty": 0,
            "closing_in_stock_qty": closing["qty"] if closing else 0,
            "closing_asset_amount": closing["amount"] if closing else None,
        })
    return items


def get_daily_ledger_breakdown(
    db: Session,
    snapshot_date: date,
    dimension: str,
    sku_id: int | None = None,
) -> list[dict]:
    """按维度汇总某日库存流水明细（SKU / 库存属性）。"""
    if dimension not in ("sku", "stock_condition"):
        raise ValueError("dimension 仅支持 sku 或 stock_condition")

    if dimension == "stock_condition" and sku_id is not None:
        return get_daily_ledger_sku_condition_breakdown(db, snapshot_date, sku_id)

    prev_date = _prev_summary_date(db, snapshot_date)
    opening_by_sku = _group_snapshots_by_sku(db, prev_date) if prev_date else {}
    closing_by_sku = _group_snapshots_by_sku(db, snapshot_date)
    inbound_by_sku = _day_inbound_by_sku(db, snapshot_date)
    outbound_by_sku = _day_outbound_by_sku(db, snapshot_date)

    if dimension == "sku":
        all_skus = _all_product_skus(db)
        items = []
        for sku_id in sorted(all_skus, key=lambda sid: all_skus[sid]):
            sku_name = all_skus[sku_id]
            opening = opening_by_sku.get(sku_id)
            closing = closing_by_sku.get(sku_id)
            items.append({
                "dimension_key": str(sku_id),
                "dimension_label": sku_name,
                "opening_in_stock_qty": opening["qty"] if opening else (None if prev_date is None else 0),
                "inbound_qty": inbound_by_sku.get(sku_id, {}).get("qty", 0),
                "outbound_qty": outbound_by_sku.get(sku_id, {}).get("qty", 0),
                "closing_in_stock_qty": closing["qty"] if closing else 0,
                "closing_asset_amount": closing["amount"] if closing else None,
            })
        return items

    opening_by_condition = _group_snapshots_by_condition(db, prev_date) if prev_date else {}
    closing_by_condition = _group_snapshots_by_condition(db, snapshot_date)
    inbound_by_condition = _day_inbound_by_condition(db, snapshot_date)

    all_conditions = set(opening_by_condition) | set(closing_by_condition) | set(inbound_by_condition)
    items = []
    for condition in sorted(all_conditions, key=lambda c: _condition_label(c)):
        opening = opening_by_condition.get(condition)
        closing = closing_by_condition.get(condition)
        items.append({
            "dimension_key": condition,
            "dimension_label": _condition_label(condition),
            "opening_in_stock_qty": opening["qty"] if opening else (None if prev_date is None else 0),
            "inbound_qty": inbound_by_condition.get(condition, 0),
            "outbound_qty": 0,
            "closing_in_stock_qty": closing["qty"] if closing else 0,
            "closing_asset_amount": closing["amount"] if closing else None,
        })
    return items


def _apply_snapshot_filters(
    query,
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
):
    if item_sn:
        query = query.filter(InventoryItemSnapshot.item_sn.like(f"%{item_sn}%"))
    if sku_id:
        query = query.filter(InventoryItemSnapshot.sku_id == sku_id)
    if category_id:
        query = query.filter(ProductSku.category_id == category_id)
    if keyword:
        query = query.filter(
            or_(
                InventoryItemSnapshot.item_sn.like(f"%{keyword}%"),
                ProductSku.name.like(f"%{keyword}%"),
            )
        )
    if stock_status:
        if stock_status == "OUT":
            query = query.filter(InventoryItemSnapshot.stock_status != StockStatus.IN_STOCK.value)
        else:
            query = query.filter(InventoryItemSnapshot.stock_status == stock_status)
    if stock_condition:
        query = query.filter(InventoryItemSnapshot.stock_condition == stock_condition)
    if operation_status:
        query = query.filter(InventoryItemSnapshot.operation_status == operation_status)
    if last_order_no:
        query = query.filter(InventoryItemSnapshot.last_order_no.like(f"%{last_order_no}%"))
    return query


def _build_snapshot_items_query(
    db: Session,
    *,
    snapshot_date: date,
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
):
    """构建日快照明细查询。"""
    query = (
        db.query(InventoryItemSnapshot, ProductSku.name.label("sku_name"))
        .join(ProductSku, InventoryItemSnapshot.sku_id == ProductSku.id)
        .filter(
            InventoryItemSnapshot.snapshot_date == snapshot_date,
            InventoryItemSnapshot.snapshot_type == SNAPSHOT_TYPE_DAILY,
        )
    )
    return _apply_snapshot_filters(
        query,
        item_sn=item_sn,
        sku_id=sku_id,
        stock_status=stock_status,
        stock_condition=stock_condition,
        operation_status=operation_status,
        last_order_no=last_order_no,
        category_id=category_id,
        keyword=keyword,
    )


def _rows_to_items(db: Session, rows) -> list[dict]:
    items = []
    for snap, sku_name in rows:
        items.append({**{c.name: getattr(snap, c.name) for c in snap.__table__.columns}, "sku_name": sku_name})
    _attach_partner_info(items, db)
    _attach_order_remark(items, db)
    return items


def _get_snapshot_items(
    db: Session,
    page: int,
    page_size: int,
    **filters,
) -> tuple[int, list[dict]]:
    query = _build_snapshot_items_query(db, **filters)
    total = query.count()
    rows = (
        query.order_by(InventoryItemSnapshot.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, _rows_to_items(db, rows)


def get_snapshot_items_by_date(
    db: Session,
    snapshot_date: date,
    page: int = 1,
    page_size: int = 20,
    **filters,
) -> tuple[int, list[dict]]:
    """按日期分页查询日快照明细。"""
    return _get_snapshot_items(db, page, page_size, snapshot_date=snapshot_date, **filters)


def get_all_snapshot_items_by_date(db: Session, snapshot_date: date, **filters) -> list[dict]:
    query = _build_snapshot_items_query(db, snapshot_date=snapshot_date, **filters)
    rows = query.order_by(InventoryItemSnapshot.id).all()
    return _rows_to_items(db, rows)


def export_snapshot_items_xlsx(db: Session, *, snapshot_date: date, **filters) -> bytes:
    """导出日快照明细 Excel。"""
    items = get_all_snapshot_items_by_date(db, snapshot_date, **filters)
    title = f"库存快照明细_{snapshot_date.isoformat()}"
    return build_items_xlsx(items, sheet_title=title)
