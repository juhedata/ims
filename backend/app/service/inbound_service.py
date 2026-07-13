from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.enums import (
    InboundMode,
    OUTBOUND_TO_STOCK_STATUS,
    OperationStatus,
    OutboundType,
    RETURN_CONDITION_ALLOWED_OUTBOUND,
    RETURN_CONDITION_EXPECTED_STOCK,
    RETURN_CONDITION_TO_OUTBOUND,
    StockCondition,
    StockStatus,
    SnSource,
    parse_outbound_type,
)
from app.models.inbound import InboundOrder, InboundOrderItem, InboundOrderLine
from app.models.inventory import InventoryItem
from app.models.outbound import OutboundOrder, OutboundOrderItem
from app.models.partner import Partner
from app.models.product import ProductSku
from app.schemas.inbound import InboundOrderCreate, InboundOrderUpdate, InboundLineCreate
from app.service.inventory_service import _keyword_filter, record_history
from app.service.partner_service import validate_partner
from app.utils.order_no import generate_inbound_no
from app.utils.sn_generator import generate_sn, sn_timestamp, validate_sn_unique


def _calc_total_qty(lines: list) -> int:
    return sum(line.quantity for line in lines)


def get_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    operation_status: str | None = None,
    inbound_mode: str | None = None,
    order_no: str | None = None,
    partner_id: int | None = None,
    stock_condition: str | None = None,
    sku_id: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    query = db.query(InboundOrder).options(joinedload(InboundOrder.partner).joinedload(Partner.group))
    if operation_status:
        query = query.filter(InboundOrder.operation_status == operation_status)
    if inbound_mode:
        query = query.filter(InboundOrder.inbound_mode == inbound_mode)
    if order_no:
        query = query.filter(InboundOrder.order_no.like(f"%{order_no}%"))
    if partner_id:
        query = query.filter(InboundOrder.partner_id == partner_id)
    if stock_condition:
        query = query.filter(InboundOrder.stock_condition == stock_condition)
    if sku_id:
        order_ids = (
            db.query(InboundOrderLine.inbound_order_id)
            .filter(InboundOrderLine.sku_id == sku_id)
            .distinct()
        )
        query = query.filter(InboundOrder.id.in_(order_ids))
    if start_time:
        query = query.filter(InboundOrder.created_at >= start_time)
    if end_time:
        query = query.filter(InboundOrder.created_at <= end_time)
    total = query.count()
    items = query.order_by(InboundOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def get_order_detail(db: Session, order_id: int | str) -> InboundOrder | None:
    query = (
        db.query(InboundOrder)
        .options(
            joinedload(InboundOrder.lines),
            joinedload(InboundOrder.items)
            .joinedload(InboundOrderItem.line)
            .joinedload(InboundOrderLine.sku),
        )
    )
    if isinstance(order_id, str) and not order_id.isdigit():
        return query.filter(InboundOrder.order_no == order_id).first()
    return query.filter(InboundOrder.id == int(order_id)).first()


def _build_procurement_items(db: Session, order: InboundOrder, lines_data: list[InboundLineCreate]) -> None:
    """构建采购入库明细和 SN 绑定。"""
    for line_data in lines_data:
        sku = db.get(ProductSku, line_data.sku_id)
        if not sku:
            raise ValueError(f"SKU 不存在：{line_data.sku_id}")

        if line_data.unit_price is None:
            raise ValueError(f"SKU [{sku.name}] 缺少商品单价")
        if line_data.unit_price < 0 or line_data.unit_price > Decimal("99999.99"):
            raise ValueError(f"SKU [{sku.name}] 的商品单价须在 0 ~ 99999.99 元之间")

        line = InboundOrderLine(
            inbound_order_id=order.id,
            sku_id=line_data.sku_id,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
        )
        db.add(line)
        db.flush()

        sns = list(line_data.item_sns or [])
        # 不足数量时按规则自动生成 SN：{skuId}-{时间戳}-{自增}
        if len(sns) < line_data.quantity:
            ts = sn_timestamp()
            for i in range(len(sns) + 1, line_data.quantity + 1):
                sns.append(generate_sn(sku.id, ts, i))

        if len(sns) != line_data.quantity:
            raise ValueError(f"SKU [{sku.name}] 的 SN 数量({len(sns)})与商品数量({line_data.quantity})不一致")

        dup = validate_sn_unique(db, sns)
        if dup:
            raise ValueError(f"SN 重复：{', '.join(dup)}")

        for sn in sns:
            source = SnSource.MANUAL.value if line_data.item_sns else SnSource.AUTO.value
            if line_data.item_sns:
                source = SnSource.MANUAL.value
            db.add(InboundOrderItem(
                inbound_order_id=order.id,
                line_id=line.id,
                item_sn=sn,
                sn_source=source,
            ))


def _validate_outbound_for_return(
    db: Session, outbound_order_id: int, stock_condition: str
) -> OutboundOrder:
    """校验关联出库单是否可用于非采购入库。"""
    outbound = db.get(OutboundOrder, outbound_order_id)
    if not outbound:
        raise ValueError("关联出库单不存在")
    if outbound.operation_status != OperationStatus.COMPLETED.value:
        raise ValueError("关联出库单必须为已完成状态")
    try:
        condition = StockCondition(stock_condition)
    except ValueError:
        raise ValueError(f"无效的入库类型：{stock_condition}") from None
    allowed_types = RETURN_CONDITION_ALLOWED_OUTBOUND.get(condition)
    if allowed_types and parse_outbound_type(outbound.outbound_type) not in allowed_types:
        expected = " / ".join(t.value for t in allowed_types)
        raise ValueError(f"入库类型与出库单类型不匹配，期望出库类型：{expected}")
    return outbound


def _pending_return_item_ids(db: Session, exclude_inbound_order_id: int | None = None) -> set[int]:
    """获取已被其他未完成入库单占用的退货单品 ID。"""
    query = (
        db.query(InboundOrderItem.item_id)
        .join(InboundOrder, InboundOrderItem.inbound_order_id == InboundOrder.id)
        .filter(
            InboundOrder.inbound_mode == InboundMode.NON_PROCUREMENT.value,
            InboundOrder.operation_status.in_([
                OperationStatus.INITIATED.value,
                OperationStatus.CHECKING.value,
            ]),
            InboundOrderItem.item_id.isnot(None),
        )
    )
    if exclude_inbound_order_id:
        query = query.filter(InboundOrder.id != exclude_inbound_order_id)
    return {r[0] for r in query.all()}


def _expected_return_stock_statuses(stock_condition: str, outbound: OutboundOrder) -> list[str]:
    """根据入库类型与出库单推断可退货单品的库存状态。"""
    try:
        condition = StockCondition(stock_condition)
    except ValueError:
        raise ValueError(f"无效的入库类型：{stock_condition}") from None
    expected_stocks = [
        status.value for status in RETURN_CONDITION_EXPECTED_STOCK.get(condition, [])
    ]
    if not expected_stocks:
        expected_stocks = [
            OUTBOUND_TO_STOCK_STATUS[parse_outbound_type(outbound.outbound_type)].value
        ]
    return expected_stocks


def _build_returnable_items_query(
    db: Session,
    outbound_order_id: int,
    stock_condition: str,
    exclude_inbound_order_id: int | None = None,
    keyword: str | None = None,
    sku_id: int | None = None,
    category_id: int | None = None,
):
    """构建关联出库单可退货单品查询（SQL 层筛选，支持分页与模糊搜索）。"""
    outbound = _validate_outbound_for_return(db, outbound_order_id, stock_condition)
    expected_stocks = _expected_return_stock_statuses(stock_condition, outbound)
    pending_ids = _pending_return_item_ids(db, exclude_inbound_order_id)

    query = (
        db.query(InventoryItem, ProductSku.name.label("sku_name"), OutboundOrderItem.sku_id)
        .join(OutboundOrderItem, OutboundOrderItem.item_id == InventoryItem.id)
        .join(ProductSku, ProductSku.id == OutboundOrderItem.sku_id)
        .filter(
            OutboundOrderItem.outbound_order_id == outbound_order_id,
            InventoryItem.stock_status.in_(expected_stocks),
            InventoryItem.operation_status == OperationStatus.COMPLETED.value,
        )
    )
    if pending_ids:
        query = query.filter(~InventoryItem.id.in_(pending_ids))
    if sku_id:
        query = query.filter(OutboundOrderItem.sku_id == sku_id)
    if category_id:
        query = query.filter(ProductSku.category_id == category_id)
    if keyword:
        cond = _keyword_filter(InventoryItem.item_sn, ProductSku.name, keyword)
        if cond is not None:
            query = query.filter(cond)
    return query


def get_returnable_items(
    db: Session,
    outbound_order_id: int,
    stock_condition: str,
    exclude_inbound_order_id: int | None = None,
    keyword: str | None = None,
    sku_id: int | None = None,
    category_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[int, list[dict]]:
    """
    分页查询关联出库单中仍可退货的单品（支持部分退货、SN 模糊搜索）。

    条件：属于该出库单、仍为出库状态（未退回在库）、未被其他待审入库单占用。
    """
    query = _build_returnable_items_query(
        db,
        outbound_order_id,
        stock_condition,
        exclude_inbound_order_id,
        keyword,
        sku_id,
        category_id,
    )
    total = query.count()
    rows = (
        query.order_by(InventoryItem.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for inv, sku_name, sku_id_val in rows:
        result.append({
            "item_id": inv.id,
            "item_sn": inv.item_sn,
            "sku_id": sku_id_val,
            "sku_name": sku_name or "",
            "stock_status": inv.stock_status,
            "stock_condition": inv.stock_condition,
        })
    return total, result


def _validate_return_item_ids(
    db: Session,
    outbound_order_id: int,
    stock_condition: str,
    return_item_ids: list[int],
    exclude_inbound_order_id: int | None = None,
) -> None:
    """校验勾选的单品均可退货。"""
    if not return_item_ids:
        raise ValueError("请至少选择一件退货商品")
    if len(return_item_ids) != len(set(return_item_ids)):
        raise ValueError("退货明细存在重复单品")

    query = _build_returnable_items_query(
        db,
        outbound_order_id,
        stock_condition,
        exclude_inbound_order_id,
    ).filter(InventoryItem.id.in_(return_item_ids))
    found_ids = {inv.id for inv, _, _ in query.all()}
    for item_id in return_item_ids:
        if item_id not in found_ids:
            raise ValueError(f"单品 [{item_id}] 不可退货（可能已退回或正在其他入库单处理中）")


def _build_non_procurement_items(
    db: Session,
    order: InboundOrder,
    outbound_order_id: int,
    return_item_ids: list[int],
) -> None:
    """非采购入库：按用户勾选的单品构建明细（支持部分退货）。"""
    _validate_return_item_ids(
        db, outbound_order_id, order.stock_condition, return_item_ids, order.id
    )

    # 查出勾选单品对应的出库明细
    ob_items = (
        db.query(OutboundOrderItem)
        .filter(
            OutboundOrderItem.outbound_order_id == outbound_order_id,
            OutboundOrderItem.item_id.in_(return_item_ids),
        )
        .all()
    )
    if len(ob_items) != len(return_item_ids):
        raise ValueError("部分勾选单品不属于该出库单")

    # 按 SKU 聚合行
    sku_items: dict[int, list[OutboundOrderItem]] = {}
    for obi in ob_items:
        sku_items.setdefault(obi.sku_id, []).append(obi)

    for sku_id, obi_list in sku_items.items():
        line = InboundOrderLine(
            inbound_order_id=order.id, sku_id=sku_id, quantity=len(obi_list)
        )
        db.add(line)
        db.flush()
        for obi in obi_list:
            inv = db.get(InventoryItem, obi.item_id)
            db.add(InboundOrderItem(
                inbound_order_id=order.id,
                line_id=line.id,
                item_id=inv.id,
                item_sn=inv.item_sn,
                sn_source=SnSource.MANUAL.value,
            ))


def create_order(db: Session, data: InboundOrderCreate, user_id: int) -> InboundOrder:
    """新建入库单（暂存状态）。"""
    validate_partner(db, data.partner_id)
    order_no = data.order_no or generate_inbound_no(db)
    if db.query(InboundOrder).filter(InboundOrder.order_no == order_no).first():
        raise ValueError(f"入库单号已存在：{order_no}")

    order = InboundOrder(
        order_no=order_no,
        inbound_mode=data.inbound_mode.value,
        stock_condition=data.stock_condition.value,
        partner_id=data.partner_id,
        related_outbound_order_id=data.related_outbound_order_id,
        remark=data.remark,
        operation_status=OperationStatus.INITIATED.value,
        submitted_by=user_id,
    )
    db.add(order)
    db.flush()

    if data.inbound_mode == InboundMode.PROCUREMENT:
        if not data.lines:
            raise ValueError("采购入库必须填写商品明细")
        _build_procurement_items(db, order, data.lines)
    else:
        if not data.related_outbound_order_id:
            raise ValueError("非采购入库必须选择关联出库单")
        if not data.return_item_ids:
            raise ValueError("非采购入库须勾选退货商品")
        _build_non_procurement_items(db, order, data.related_outbound_order_id, data.return_item_ids)

    order.total_qty = _calc_total_qty(order.lines) if order.lines else (
        db.query(InboundOrderLine).filter(InboundOrderLine.inbound_order_id == order.id).count()
    )
    # 重新计算 total_qty
    lines = db.query(InboundOrderLine).filter(InboundOrderLine.inbound_order_id == order.id).all()
    order.total_qty = sum(l.quantity for l in lines)

    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order: InboundOrder, data: InboundOrderUpdate) -> InboundOrder:
    """修改入库单（仅 INITIATED 且未提交审核）。"""
    if order.operation_status != OperationStatus.INITIATED.value:
        raise ValueError("仅待处理状态的单据可修改")
    if order.submitted_at is not None:
        raise ValueError("已提交审核的单据不可修改")

    update_data = data.model_dump(exclude_none=True, exclude={"lines", "return_item_ids"})
    if "partner_id" in update_data:
        validate_partner(db, update_data["partner_id"])
    for k, v in update_data.items():
        setattr(order, k, v.value if hasattr(v, "value") else v)

    rebuild = data.lines is not None or data.return_item_ids is not None
    if rebuild:
        db.query(InboundOrderItem).filter(InboundOrderItem.inbound_order_id == order.id).delete()
        db.query(InboundOrderLine).filter(InboundOrderLine.inbound_order_id == order.id).delete()
        db.flush()
        if order.inbound_mode == InboundMode.PROCUREMENT.value:
            if data.lines is None:
                raise ValueError("采购入库修改须提供商品明细")
            _build_procurement_items(db, order, data.lines)
        else:
            outbound_id = data.related_outbound_order_id or order.related_outbound_order_id
            if not outbound_id:
                raise ValueError("非采购入库必须有关联出库单")
            order.related_outbound_order_id = outbound_id
            item_ids = data.return_item_ids
            if not item_ids:
                raise ValueError("非采购入库须勾选退货商品")
            _build_non_procurement_items(db, order, outbound_id, item_ids)

    lines = db.query(InboundOrderLine).filter(InboundOrderLine.inbound_order_id == order.id).all()
    order.total_qty = sum(l.quantity for l in lines)
    db.commit()
    db.refresh(order)
    return order


def submit_order(db: Session, order: InboundOrder, user_id: int) -> InboundOrder:
    """提交待审核。"""
    if order.operation_status != OperationStatus.INITIATED.value:
        raise ValueError("当前状态不可提交")
    if order.submitted_at is not None:
        raise ValueError("单据已提交")
    validate_partner(db, order.partner_id)

    # 锁定关联单品
    for oi in order.items:
        if oi.item_id:
            inv = db.get(InventoryItem, oi.item_id)
            if inv:
                inv.operation_status = OperationStatus.CHECKING.value
        # 采购全新入库再次校验 SN
        if order.inbound_mode == InboundMode.PROCUREMENT.value:
            dup = validate_sn_unique(db, [oi.item_sn], exclude_order_id=order.id)
            if dup:
                raise ValueError(f"SN 重复：{', '.join(dup)}")

    order.submitted_at = datetime.now()
    order.submitted_by = user_id
    db.commit()
    db.refresh(order)
    return order


def approve_order(db: Session, order: InboundOrder, user_id: int) -> InboundOrder:
    """审核通过。"""
    if order.operation_status != OperationStatus.INITIATED.value or order.submitted_at is None:
        raise ValueError("仅已提交待审核的单据可审核")

    order.operation_status = OperationStatus.COMPLETED.value
    order.reviewed_by = user_id
    order.reviewed_at = datetime.now()

    if order.inbound_mode == InboundMode.PROCUREMENT.value:
        for oi in order.items:
            line = db.get(InboundOrderLine, oi.line_id)
            inv = InventoryItem(
                item_sn=oi.item_sn,
                sku_id=line.sku_id,
                stock_status=StockStatus.IN_STOCK.value,
                stock_condition=order.stock_condition,
                operation_status=OperationStatus.COMPLETED.value,
                last_order_no=order.order_no,
                unit_price=line.unit_price,
            )
            db.add(inv)
            db.flush()
            oi.item_id = inv.id
            record_history(db, inv, "INBOUND", order.order_no, user_id,
                           to_stock=StockStatus.IN_STOCK.value, to_op=OperationStatus.COMPLETED.value)
    else:
        for oi in order.items:
            inv = db.get(InventoryItem, oi.item_id)
            if not inv:
                raise ValueError(f"库存单品不存在：{oi.item_id}")
            old_stock = inv.stock_status
            inv.stock_status = StockStatus.IN_STOCK.value
            inv.stock_condition = order.stock_condition
            inv.operation_status = OperationStatus.COMPLETED.value
            inv.last_order_no = order.order_no
            record_history(db, inv, "INBOUND", order.order_no, user_id,
                           from_stock=old_stock, to_stock=StockStatus.IN_STOCK.value)

    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: InboundOrder) -> InboundOrder:
    """取消/作废单据。"""
    if order.operation_status == OperationStatus.COMPLETED.value:
        raise ValueError("已完成的单据不可取消")
    if order.operation_status == OperationStatus.CANCELLED.value:
        raise ValueError("单据已取消")

    for oi in order.items:
        if oi.item_id:
            inv = db.get(InventoryItem, oi.item_id)
            if inv and inv.operation_status == OperationStatus.CHECKING.value:
                inv.operation_status = OperationStatus.COMPLETED.value

    order.operation_status = OperationStatus.CANCELLED.value
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: InboundOrder) -> None:
    """删除入库单（仅暂存/已取消）。"""
    if order.operation_status == OperationStatus.COMPLETED.value:
        raise ValueError("已完成的单据不可删除")
    if order.submitted_at is not None and order.operation_status == OperationStatus.INITIATED.value:
        raise ValueError("已提交待审核的单据不可删除，请先取消")
    db.delete(order)
    db.commit()
