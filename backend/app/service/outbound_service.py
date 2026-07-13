from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.enums import OUTBOUND_TO_STOCK_STATUS, OperationStatus, StockStatus
from app.models.inventory import InventoryItem
from app.models.outbound import OutboundOrder, OutboundOrderItem
from app.models.partner import Partner
from app.models.product import ProductCategory, ProductSku
from app.schemas.outbound import OutboundOrderCreate, OutboundOrderResponse, OutboundOrderUpdate
from app.service.inventory_service import record_history
from app.service import customer_service
from app.service.partner_service import validate_partner
from app.utils.order_no import generate_outbound_no


def get_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    operation_status: str | None = None,
    outbound_type: str | None = None,
    order_no: str | None = None,
    partner_id: int | None = None,
    sku_id: int | None = None,
    item_sn: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    query = db.query(OutboundOrder).options(joinedload(OutboundOrder.partner).joinedload(Partner.group))
    if operation_status:
        query = query.filter(OutboundOrder.operation_status == operation_status)
    if outbound_type:
        query = query.filter(OutboundOrder.outbound_type == outbound_type)
    if order_no:
        query = query.filter(OutboundOrder.order_no.like(f"%{order_no}%"))
    if partner_id:
        query = query.filter(OutboundOrder.partner_id == partner_id)
    if sku_id:
        order_ids = (
            db.query(OutboundOrderItem.outbound_order_id)
            .filter(OutboundOrderItem.sku_id == sku_id)
            .distinct()
        )
        query = query.filter(OutboundOrder.id.in_(order_ids))
    if item_sn and item_sn.strip():
        sn = item_sn.strip()
        order_ids = (
            db.query(OutboundOrderItem.outbound_order_id)
            .join(InventoryItem, OutboundOrderItem.item_id == InventoryItem.id)
            .filter(InventoryItem.item_sn.like(f"%{sn}%"))
            .distinct()
        )
        query = query.filter(OutboundOrder.id.in_(order_ids))
    if start_time:
        query = query.filter(OutboundOrder.created_at >= start_time)
    if end_time:
        query = query.filter(OutboundOrder.created_at <= end_time)
    total = query.count()
    items = query.order_by(OutboundOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def get_order_detail(db: Session, order_id: int | str) -> OutboundOrder | None:
    query = (
        db.query(OutboundOrder)
        .options(
            joinedload(OutboundOrder.items),
            joinedload(OutboundOrder.partner).joinedload(Partner.group),
        )
    )
    if isinstance(order_id, str) and not order_id.isdigit():
        return query.filter(OutboundOrder.order_no == order_id).first()
    return query.filter(OutboundOrder.id == int(order_id)).first()


def order_to_response(db: Session, order: OutboundOrder) -> OutboundOrderResponse:
    """组装出库单详情（含单品与 SKU 信息）。"""
    item_rows = []
    for oi in order.items:
        inv = db.get(InventoryItem, oi.item_id)
        sku = db.get(ProductSku, oi.sku_id)
        category_name = None
        if sku:
            category = db.get(ProductCategory, sku.category_id)
            category_name = category.name if category else None
        item_rows.append({
            "id": oi.id,
            "item_id": oi.item_id,
            "sku_id": oi.sku_id,
            "quantity": oi.quantity,
            "item_sn": inv.item_sn if inv else None,
            "sku_name": sku.name if sku else None,
            "sku_unit": sku.unit if sku else None,
            "barcode": sku.barcode if sku else None,
            "category_name": category_name,
            "stock_status": inv.stock_status if inv else None,
            "stock_condition": inv.stock_condition if inv else None,
            "operation_status": inv.operation_status if inv else None,
        })
    data = {c.name: getattr(order, c.name) for c in order.__table__.columns}
    data["partner_name"] = order.partner_name
    data["partner_group_id"] = order.partner_group_id
    data["partner_group_name"] = order.partner_group_name
    data["items"] = item_rows
    return OutboundOrderResponse(**data)


def _item_ids_in_active_outbound(db: Session, exclude_order_id: int | None = None) -> set[int]:
    """获取未完成出库单已占用的单品 ID。"""
    query = (
        db.query(OutboundOrderItem.item_id)
        .join(OutboundOrder, OutboundOrderItem.outbound_order_id == OutboundOrder.id)
        .filter(OutboundOrder.operation_status == OperationStatus.INITIATED.value)
    )
    if exclude_order_id is not None:
        query = query.filter(OutboundOrder.id != exclude_order_id)
    return {row[0] for row in query.all()}


def _validate_outbound_items(
    db: Session,
    item_ids: list[int],
    exclude_order_id: int | None = None,
) -> list[InventoryItem]:
    """校验单品可出库（在库、未被其他出库单占用）。"""
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("出库明细存在重复单品")

    busy_ids = _item_ids_in_active_outbound(db, exclude_order_id)
    items: list[InventoryItem] = []
    for item_id in item_ids:
        if item_id in busy_ids:
            inv = db.get(InventoryItem, item_id)
            sn = inv.item_sn if inv else str(item_id)
            raise ValueError(f"单品 [{sn}] 已被其他出库单占用")
        inv = db.get(InventoryItem, item_id)
        if not inv:
            raise ValueError(f"库存单品不存在：{item_id}")
        if inv.stock_status != StockStatus.IN_STOCK.value:
            raise ValueError(f"单品 [{inv.item_sn}] 不在库，当前状态：{inv.stock_status}")
        if inv.operation_status != OperationStatus.COMPLETED.value:
            raise ValueError(f"单品 [{inv.item_sn}] 正在其他单据处理中")
        items.append(inv)
    return items


def _lock_outbound_items(inv_items: list[InventoryItem]) -> None:
    """暂存/修改出库单时锁定单品。"""
    for inv in inv_items:
        inv.operation_status = OperationStatus.PICKING.value


def _release_outbound_items(db: Session, order: OutboundOrder) -> None:
    """删除/取消/修改出库单时释放在库单品的出库锁定。"""
    for oi in order.items:
        inv = db.get(InventoryItem, oi.item_id)
        if (
            inv
            and inv.stock_status == StockStatus.IN_STOCK.value
            and inv.operation_status == OperationStatus.PICKING.value
        ):
            inv.operation_status = OperationStatus.COMPLETED.value


def _assert_items_locked_for_order(order: OutboundOrder, db: Session) -> None:
    """提交/审核前确认单品仍由本单锁定且在库。"""
    for oi in order.items:
        inv = db.get(InventoryItem, oi.item_id)
        if not inv:
            raise ValueError(f"库存单品不存在：{oi.item_id}")
        if inv.stock_status != StockStatus.IN_STOCK.value:
            raise ValueError(f"单品 [{inv.item_sn}] 不在库，无法出库")
        if inv.operation_status != OperationStatus.PICKING.value:
            raise ValueError(f"单品 [{inv.item_sn}] 未处于出库锁定状态")


def _resolve_customer_name(db: Session, customer_name: str | None) -> str:
    """规范化客户名称，并在客户表中自动建档。"""
    if customer_name is None:
        raise ValueError("请填写客户名称")
    name = customer_name.strip()
    if not name:
        raise ValueError("客户名称不能为空")
    customer_service.get_or_create(db, name)
    return name


def _assert_customer_name(order: OutboundOrder) -> None:
    if not order.customer_name or not order.customer_name.strip():
        raise ValueError("请填写客户名称")


def create_order(db: Session, data: OutboundOrderCreate, user_id: int) -> OutboundOrder:
    """新建出库单（暂存）。"""
    validate_partner(db, data.partner_id)
    if not data.item_ids:
        raise ValueError("请选择出库商品")

    order_no = data.order_no or generate_outbound_no(db)
    if db.query(OutboundOrder).filter(OutboundOrder.order_no == order_no).first():
        raise ValueError(f"出库单号已存在：{order_no}")

    inv_items = _validate_outbound_items(db, data.item_ids)
    _lock_outbound_items(inv_items)

    customer_name = _resolve_customer_name(db, data.customer_name)

    order = OutboundOrder(
        order_no=order_no,
        outbound_type=data.outbound_type.value,
        partner_id=data.partner_id,
        customer_name=customer_name,
        remark=data.remark,
        operation_status=OperationStatus.INITIATED.value,
        total_qty=len(data.item_ids),
        submitted_by=user_id,
    )
    db.add(order)
    db.flush()

    for inv in inv_items:
        db.add(OutboundOrderItem(
            outbound_order_id=order.id,
            item_id=inv.id,
            sku_id=inv.sku_id,
            quantity=1,
        ))

    customer_service.increment_weight(db, customer_name)

    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order: OutboundOrder, data: OutboundOrderUpdate) -> OutboundOrder:
    """修改出库单（仅暂存）。"""
    if order.operation_status != OperationStatus.INITIATED.value:
        raise ValueError("仅待处理状态的单据可修改")
    if order.submitted_at is not None:
        raise ValueError("已提交审核的单据不可修改")

    update_data = data.model_dump(exclude_none=True, exclude={"item_ids"})
    if "customer_name" in data.model_dump(exclude_unset=True):
        update_data["customer_name"] = _resolve_customer_name(db, data.customer_name)
    if "partner_id" in update_data:
        validate_partner(db, update_data["partner_id"])
    for k, v in update_data.items():
        setattr(order, k, v.value if hasattr(v, "value") else v)

    if data.item_ids is not None:
        _release_outbound_items(db, order)
        db.query(OutboundOrderItem).filter(OutboundOrderItem.outbound_order_id == order.id).delete()
        db.flush()
        inv_items = _validate_outbound_items(db, data.item_ids, exclude_order_id=order.id)
        _lock_outbound_items(inv_items)
        for inv in inv_items:
            db.add(OutboundOrderItem(
                outbound_order_id=order.id,
                item_id=inv.id,
                sku_id=inv.sku_id,
                quantity=1,
            ))
        order.total_qty = len(data.item_ids)

    _assert_customer_name(order)

    customer_service.increment_weight(db, order.customer_name)

    db.commit()
    db.refresh(order)
    return order


def submit_order(db: Session, order: OutboundOrder, user_id: int) -> OutboundOrder:
    """提交待审核。"""
    if order.operation_status != OperationStatus.INITIATED.value:
        raise ValueError("当前状态不可提交")
    if order.submitted_at is not None:
        raise ValueError("单据已提交")
    validate_partner(db, order.partner_id)
    _assert_customer_name(order)
    _assert_items_locked_for_order(order, db)

    order.submitted_at = datetime.now()
    order.submitted_by = user_id
    db.commit()
    db.refresh(order)
    return order


def approve_order(db: Session, order: OutboundOrder, user_id: int) -> OutboundOrder:
    """审核通过，更新单品库存状态。"""
    if order.operation_status != OperationStatus.INITIATED.value or order.submitted_at is None:
        raise ValueError("仅已提交待审核的单据可审核")

    from app.models.enums import OutboundType, parse_outbound_type
    try:
        ob_type = parse_outbound_type(order.outbound_type)
        target_status = OUTBOUND_TO_STOCK_STATUS[ob_type]
    except (ValueError, KeyError):
        raise ValueError(f"无效的出库类型：{order.outbound_type}")

    order.operation_status = OperationStatus.COMPLETED.value
    order.reviewed_by = user_id
    order.reviewed_at = datetime.now()

    for oi in order.items:
        inv = db.get(InventoryItem, oi.item_id)
        if not inv:
            raise ValueError(f"库存单品不存在：{oi.item_id}")
        if inv.stock_status != StockStatus.IN_STOCK.value:
            raise ValueError(f"单品 [{inv.item_sn}] 不在库，无法审核出库")
        if inv.operation_status != OperationStatus.PICKING.value:
            raise ValueError(f"单品 [{inv.item_sn}] 未处于出库锁定状态")
        old_stock = inv.stock_status
        inv.stock_status = target_status.value
        inv.operation_status = OperationStatus.COMPLETED.value
        inv.last_order_no = order.order_no
        record_history(db, inv, "OUTBOUND", order.order_no, user_id,
                       from_stock=old_stock, to_stock=target_status.value)

    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: OutboundOrder) -> OutboundOrder:
    """取消出库单，释放单品锁定。"""
    if order.operation_status == OperationStatus.COMPLETED.value:
        raise ValueError("已完成的单据不可取消")
    if order.operation_status == OperationStatus.CANCELLED.value:
        raise ValueError("单据已取消")

    for oi in order.items:
        inv = db.get(InventoryItem, oi.item_id)
        if (
            inv
            and inv.stock_status == StockStatus.IN_STOCK.value
            and inv.operation_status == OperationStatus.PICKING.value
        ):
            inv.operation_status = OperationStatus.COMPLETED.value

    order.operation_status = OperationStatus.CANCELLED.value
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: OutboundOrder) -> None:
    """删除出库单。"""
    if order.operation_status == OperationStatus.COMPLETED.value:
        raise ValueError("已完成的单据不可删除")
    if order.submitted_at is not None and order.operation_status == OperationStatus.INITIATED.value:
        raise ValueError("已提交待审核的单据不可删除，请先取消")
    _release_outbound_items(db, order)
    db.delete(order)
    db.commit()
