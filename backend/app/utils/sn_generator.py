from datetime import datetime

from sqlalchemy.orm import Session

from app.models.inventory import InventoryItem


def sn_timestamp(dt: datetime | None = None) -> str:
    """生成 SN 时间戳：YYMMDDHHmmss（与前端一致）。"""
    dt = dt or datetime.now()
    return dt.strftime("%y%m%d%H%M%S")


def generate_sn(sku_id: int, ts: str, item_seq: int) -> str:
    """
    按规则生成 SN：{skuId}-{时间戳}-{自增3位}，与前端生成格式一致。
    例：12-260614113100-001
    """
    return f"{sku_id}-{ts}-{item_seq:03d}"


def validate_sn_unique(db: Session, sns: list[str], exclude_order_id: int | None = None) -> list[str]:
    """
    批量校验 SN 唯一性，返回重复的 SN 列表。
    检查：库存已有 + 其他未完成入库单中已录入。
    """
    from app.models.inbound import InboundOrderItem, InboundOrder
    from app.models.enums import OperationStatus

    duplicates: list[str] = []
    seen: set[str] = set()

    for sn in sns:
        if sn in seen:
            duplicates.append(sn)
        seen.add(sn)

    if not sns:
        return duplicates

    # 库存中已存在
    existing = (
        db.query(InventoryItem.item_sn)
        .filter(InventoryItem.item_sn.in_(sns))
        .all()
    )
    duplicates.extend([r[0] for r in existing])

    # 其他未完成入库单中已录入
    pending_query = (
        db.query(InboundOrderItem.item_sn)
        .join(InboundOrder, InboundOrderItem.inbound_order_id == InboundOrder.id)
        .filter(
            InboundOrderItem.item_sn.in_(sns),
            InboundOrder.operation_status.in_([
                OperationStatus.INITIATED,
                OperationStatus.CHECKING,
            ]),
        )
    )
    if exclude_order_id:
        pending_query = pending_query.filter(InboundOrder.id != exclude_order_id)
    pending = pending_query.all()
    duplicates.extend([r[0] for r in pending])

    return list(set(duplicates))
