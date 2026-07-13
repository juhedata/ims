from sqlalchemy.orm import Session

from app.models.enums import OperationStatus
from app.models.inbound import InboundOrder
from app.models.outbound import OutboundOrder
from app.service.inventory_service import get_stock_summary_by_partner, get_stock_summary_by_sku


def get_pending_audit(db: Session) -> dict:
    """待审核统计：已提交且状态为 INITIATED 的单据数。"""
    inbound_count = (
        db.query(InboundOrder)
        .filter(
            InboundOrder.operation_status == OperationStatus.INITIATED.value,
            InboundOrder.submitted_at.isnot(None),
        )
        .count()
    )
    outbound_count = (
        db.query(OutboundOrder)
        .filter(
            OutboundOrder.operation_status == OperationStatus.INITIATED.value,
            OutboundOrder.submitted_at.isnot(None),
        )
        .count()
    )
    return {"inbound_pending": inbound_count, "outbound_pending": outbound_count}


def get_stock_summary(db: Session) -> list[dict]:
    """按 SKU 库存统计表。"""
    return get_stock_summary_by_sku(db)


def get_partner_summary(db: Session, sku_ids: list[int] | None = None) -> list[dict]:
    """按关联单位统计不在库单品各状态数量。"""
    return get_stock_summary_by_partner(db, sku_ids=sku_ids)
