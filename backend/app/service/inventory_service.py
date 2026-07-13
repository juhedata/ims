from datetime import datetime

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.enums import OperationStatus, StockCondition, StockStatus
from app.models.inbound import InboundOrder
from app.models.inventory import InventoryItem, InventoryItemHistory
from app.models.outbound import OutboundOrder, OutboundOrderItem
from app.models.partner import Partner, PartnerGroup
from app.models.product import ProductSku
from app.schemas.inventory import empty_in_stock_details
from app.utils.item_export import build_items_xlsx

# 多行 SN 模糊搜索允许的最大关键词数量
MAX_KEYWORD_TOKENS = 100


def _parse_keyword_tokens(keyword: str) -> list[str]:
    """将 keyword 按行拆分为多个搜索词（去空、去重，上限 MAX_KEYWORD_TOKENS）。"""
    tokens: list[str] = []
    seen: set[str] = set()
    for line in keyword.splitlines():
        token = line.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    if len(tokens) > MAX_KEYWORD_TOKENS:
        raise ValueError(f"最多支持同时查询 {MAX_KEYWORD_TOKENS} 个 SN")
    return tokens


def _keyword_filter(item_sn_col, sku_name_col, keyword: str):
    """构建 keyword 模糊匹配条件：单行可匹配 SN 或商品名，多行仅匹配 SN（OR）。"""
    tokens = _parse_keyword_tokens(keyword)
    if not tokens:
        return None
    if len(tokens) == 1:
        token = tokens[0]
        if sku_name_col is not None:
            return or_(
                item_sn_col.like(f"%{token}%"),
                sku_name_col.like(f"%{token}%"),
            )
        return item_sn_col.like(f"%{token}%")
    return or_(*(item_sn_col.like(f"%{token}%") for token in tokens))


def _partner_map(db: Session, order_model, order_nos: set[str]) -> dict[str, dict]:
    """批量查询单号对应的往来单位及单位组；出库单额外附带客户名称。"""
    if not order_nos:
        return {}
    select_cols = [
        order_model.order_no,
        Partner.id,
        Partner.name,
        PartnerGroup.id,
        PartnerGroup.name,
    ]
    include_customer_name = order_model is OutboundOrder
    if include_customer_name:
        select_cols.append(OutboundOrder.customer_name)
    rows = (
        db.query(*select_cols)
        .join(Partner, order_model.partner_id == Partner.id)
        .join(PartnerGroup, Partner.group_id == PartnerGroup.id)
        .filter(order_model.order_no.in_(order_nos))
        .all()
    )
    result: dict[str, dict] = {}
    for row in rows:
        order_no = row[0]
        info = {
            "partner_id": row[1],
            "partner_name": row[2],
            "partner_group_id": row[3],
            "partner_group_name": row[4],
        }
        if include_customer_name:
            info["customer_name"] = row[5]
        result[order_no] = info
    return result


def _order_remark_map(db: Session, order_nos: set[str]) -> dict[str, str | None]:
    """批量查询单号对应的备注。"""
    if not order_nos:
        return {}
    inbound_nos = {no for no in order_nos if no.startswith("JIN-")}
    outbound_nos = order_nos - inbound_nos
    result: dict[str, str | None] = {}
    if inbound_nos:
        for order_no, remark in (
            db.query(InboundOrder.order_no, InboundOrder.remark)
            .filter(InboundOrder.order_no.in_(inbound_nos))
            .all()
        ):
            result[order_no] = remark
    if outbound_nos:
        for order_no, remark in (
            db.query(OutboundOrder.order_no, OutboundOrder.remark)
            .filter(OutboundOrder.order_no.in_(outbound_nos))
            .all()
        ):
            result[order_no] = remark
    return result


def _attach_order_remark(items: list[dict], db: Session) -> None:
    """为单品补充关联单号的备注。"""
    order_nos = {item["last_order_no"] for item in items if item.get("last_order_no")}
    remark_map = _order_remark_map(db, order_nos)
    for item in items:
        order_no = item.get("last_order_no")
        item["remark"] = remark_map.get(order_no) if order_no else None


def _resolve_partner_from_order_no(
    order_no: str | None,
    inbound_map: dict[str, dict],
    outbound_map: dict[str, dict],
) -> dict:
    if not order_no:
        return {}
    if order_no.startswith("JOUT-"):
        return outbound_map.get(order_no, {})
    if order_no.startswith("JIN-"):
        return inbound_map.get(order_no, {})
    return outbound_map.get(order_no) or inbound_map.get(order_no, {})


def _attach_partner_info(items: list[dict], db: Session) -> None:
    """为不在库单品补充关联单号的往来单位信息。"""
    order_nos = {
        item["last_order_no"]
        for item in items
        if item.get("stock_status") != StockStatus.IN_STOCK.value and item.get("last_order_no")
    }
    if not order_nos:
        for item in items:
            item.setdefault("partner_id", None)
            item.setdefault("partner_name", None)
            item.setdefault("partner_group_id", None)
            item.setdefault("partner_group_name", None)
            item.setdefault("customer_name", None)
        return

    inbound_nos = {no for no in order_nos if no.startswith("JIN-")}
    outbound_nos = order_nos - inbound_nos
    inbound_map = _partner_map(db, InboundOrder, inbound_nos)
    outbound_map = _partner_map(db, OutboundOrder, outbound_nos)

    for item in items:
        item.setdefault("partner_id", None)
        item.setdefault("partner_name", None)
        item.setdefault("partner_group_id", None)
        item.setdefault("partner_group_name", None)
        item.setdefault("customer_name", None)
        if item.get("stock_status") == StockStatus.IN_STOCK.value:
            continue
        order_no = item.get("last_order_no")
        partner_info = _resolve_partner_from_order_no(order_no, inbound_map, outbound_map)
        item.update({k: partner_info.get(k) for k in ("partner_id", "partner_name", "partner_group_id", "partner_group_name")})
        if order_no and order_no.startswith("JOUT-"):
            item["customer_name"] = outbound_map.get(order_no, {}).get("customer_name")


def record_history(
    db: Session,
    item: InventoryItem,
    event_type: str,
    order_no: str | None,
    operator_id: int | None,
    from_stock: str | None = None,
    to_stock: str | None = None,
    from_op: str | None = None,
    to_op: str | None = None,
    remark: str | None = None,
) -> None:
    """写入单品变动轨迹。"""
    history = InventoryItemHistory(
        item_id=item.id,
        event_type=event_type,
        order_no=order_no,
        from_stock_status=from_stock or item.stock_status,
        to_stock_status=to_stock or item.stock_status,
        from_operation_status=from_op or item.operation_status,
        to_operation_status=to_op or item.operation_status,
        operator_id=operator_id,
        remark=remark,
        created_at=datetime.now(),
    )
    db.add(history)


def _build_items_query(
    db: Session,
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
):
    """构建库存单品查询（含筛选条件）。"""
    query = (
        db.query(InventoryItem, ProductSku.name.label("sku_name"))
        .join(ProductSku, InventoryItem.sku_id == ProductSku.id)
    )
    if item_sn:
        query = query.filter(InventoryItem.item_sn.like(f"%{item_sn}%"))
    if sku_id:
        query = query.filter(InventoryItem.sku_id == sku_id)
    if category_id:
        query = query.filter(ProductSku.category_id == category_id)
    if keyword:
        cond = _keyword_filter(InventoryItem.item_sn, ProductSku.name, keyword)
        if cond is not None:
            query = query.filter(cond)
    if stock_status:
        if stock_status == "OUT":
            # 出库整体：所有非在库状态
            query = query.filter(InventoryItem.stock_status != StockStatus.IN_STOCK.value)
        else:
            query = query.filter(InventoryItem.stock_status == stock_status)
    if stock_condition:
        query = query.filter(InventoryItem.stock_condition == stock_condition)
    if operation_status:
        query = query.filter(InventoryItem.operation_status == operation_status)
    if last_order_no:
        query = query.filter(InventoryItem.last_order_no.like(f"%{last_order_no}%"))
    return query


def _items_rows_to_dicts(db: Session, rows) -> list[dict]:
    items = []
    for item, sku_name in rows:
        items.append({**{c.name: getattr(item, c.name) for c in item.__table__.columns}, "sku_name": sku_name})
    _attach_partner_info(items, db)
    _attach_order_remark(items, db)
    return items


def get_items(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
) -> tuple[int, list[dict]]:
    """分页查询库存单品，附带 SKU 名称。"""
    query = _build_items_query(
        db,
        item_sn=item_sn,
        sku_id=sku_id,
        stock_status=stock_status,
        stock_condition=stock_condition,
        operation_status=operation_status,
        last_order_no=last_order_no,
        category_id=category_id,
        keyword=keyword,
    )
    total = query.count()
    rows = (
        query.order_by(InventoryItem.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, _items_rows_to_dicts(db, rows)


def get_all_items(
    db: Session,
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
) -> list[dict]:
    """查询全部库存单品（不分页，用于导出）。"""
    query = _build_items_query(
        db,
        item_sn=item_sn,
        sku_id=sku_id,
        stock_status=stock_status,
        stock_condition=stock_condition,
        operation_status=operation_status,
        last_order_no=last_order_no,
        category_id=category_id,
        keyword=keyword,
    )
    rows = query.order_by(InventoryItem.id.desc()).all()
    return _items_rows_to_dicts(db, rows)


def export_items_xlsx(db: Session, **filters) -> bytes:
    """导出库存单品明细为 Excel（xlsx）字节流。"""
    items = get_all_items(db, **filters)
    return build_items_xlsx(items, sheet_title="实时库存明细")


def get_item_by_sn(db: Session, item_sn: str) -> InventoryItem | None:
    """按 SN 查询单品。"""
    return db.query(InventoryItem).filter(InventoryItem.item_sn == item_sn).first()


def get_item_detail(db: Session, item: InventoryItem) -> dict:
    """单品详情，附带 SKU 名称及不在库时的往来单位。"""
    sku = db.get(ProductSku, item.sku_id)
    data = {c.name: getattr(item, c.name) for c in item.__table__.columns}
    data["sku_name"] = sku.name if sku else None
    _attach_partner_info([data], db)
    return data


def get_item_history(db: Session, item_id: int) -> list[dict]:
    """查询单品历史轨迹，附带关联单据的往来单位信息。"""
    records = (
        db.query(InventoryItemHistory)
        .filter(InventoryItemHistory.item_id == item_id)
        .order_by(InventoryItemHistory.created_at.desc())
        .all()
    )

    inbound_nos = {r.order_no for r in records if r.event_type == "INBOUND" and r.order_no}
    outbound_nos = {r.order_no for r in records if r.event_type == "OUTBOUND" and r.order_no}

    inbound_map = _partner_map(db, InboundOrder, inbound_nos)
    outbound_map = _partner_map(db, OutboundOrder, outbound_nos)

    result = []
    for r in records:
        d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        if r.event_type == "INBOUND":
            partner_info = inbound_map.get(r.order_no, {})
        elif r.event_type == "OUTBOUND":
            partner_info = outbound_map.get(r.order_no, {})
        else:
            partner_info = {}
        d.update({
            "partner_id": partner_info.get("partner_id"),
            "partner_name": partner_info.get("partner_name"),
            "partner_group_id": partner_info.get("partner_group_id"),
            "partner_group_name": partner_info.get("partner_group_name"),
        })
        result.append(d)

    return result


def get_available_items(
    db: Session,
    sku_id: int | None = None,
    item_sn: str | None = None,
    stock_condition: str | None = None,
    keyword: str | None = None,
    category_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
    outbound_order_id: int | None = None,
) -> tuple[int, list[dict]]:
    """查询可出库单品：在库且未被其他单据锁定；编辑出库单时可包含本单已锁定单品。"""
    query = (
        db.query(InventoryItem, ProductSku.name.label("sku_name"))
        .join(ProductSku, InventoryItem.sku_id == ProductSku.id)
        .filter(InventoryItem.stock_status == StockStatus.IN_STOCK.value)
    )
    if outbound_order_id:
        current_item_ids = [
            row[0]
            for row in db.query(OutboundOrderItem.item_id)
            .filter(OutboundOrderItem.outbound_order_id == outbound_order_id)
            .all()
        ]
        if current_item_ids:
            query = query.filter(
                or_(
                    InventoryItem.operation_status == OperationStatus.COMPLETED.value,
                    and_(
                        InventoryItem.id.in_(current_item_ids),
                        InventoryItem.operation_status == OperationStatus.PICKING.value,
                    ),
                )
            )
        else:
            query = query.filter(InventoryItem.operation_status == OperationStatus.COMPLETED.value)
    else:
        query = query.filter(InventoryItem.operation_status == OperationStatus.COMPLETED.value)
    if sku_id:
        query = query.filter(InventoryItem.sku_id == sku_id)
    if category_id:
        query = query.filter(ProductSku.category_id == category_id)
    if item_sn:
        query = query.filter(InventoryItem.item_sn.like(f"%{item_sn}%"))
    if stock_condition:
        query = query.filter(InventoryItem.stock_condition == stock_condition)
    if keyword:
        cond = _keyword_filter(InventoryItem.item_sn, ProductSku.name, keyword)
        if cond is not None:
            query = query.filter(cond)

    total = query.count()
    rows = query.order_by(InventoryItem.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for item, sku_name in rows:
        items.append({**{c.name: getattr(item, c.name) for c in item.__table__.columns}, "sku_name": sku_name})
    return total, items


def get_stock_summary_by_sku(db: Session) -> list[dict]:
    """按 SKU 汇总各库存状态数量。"""
    rows = (
        db.query(
            ProductSku.id,
            ProductSku.name,
            InventoryItem.stock_status,
            func.count(InventoryItem.id).label("cnt"),
        )
        .outerjoin(InventoryItem, InventoryItem.sku_id == ProductSku.id)
        .filter(ProductSku.status == 1)
        .group_by(ProductSku.id, ProductSku.name, InventoryItem.stock_status)
        .all()
    )
    in_stock_rows = (
        db.query(
            ProductSku.id,
            InventoryItem.stock_condition,
            func.count(InventoryItem.id).label("cnt"),
        )
        .join(InventoryItem, InventoryItem.sku_id == ProductSku.id)
        .filter(
            ProductSku.status == 1,
            InventoryItem.stock_status == StockStatus.IN_STOCK.value,
        )
        .group_by(ProductSku.id, InventoryItem.stock_condition)
        .all()
    )
    summary: dict[int, dict] = {}
    status_field_map = {
        StockStatus.IN_STOCK.value: "in_stock",
        StockStatus.SOLD.value: "sold",
        StockStatus.PRESOLD.value: "presold",
        StockStatus.SOLD_OFFLINE.value: "sold_offline",
        StockStatus.BORROWED.value: "borrowed",
        StockStatus.GIFTED.value: "gifted",
        StockStatus.SCRAPPED.value: "scrapped",
        StockStatus.RND.value: "rnd",
        StockStatus.SAMPLE.value: "sample",
        StockStatus.TRIAL.value: "trial",
        StockStatus.REPAIR.value: "repair",
        StockStatus.DEPT_PROCUREMENT.value: "dept_procurement",
    }
    for sku_id, sku_name, status, cnt in rows:
        if sku_id not in summary:
            summary[sku_id] = {
                "sku_id": sku_id,
                "sku_name": sku_name,
                "in_stock": 0,
                "in_stock_details": empty_in_stock_details(),
                "sold": 0,
                "presold": 0,
                "sold_offline": 0,
                "borrowed": 0,
                "gifted": 0,
                "scrapped": 0,
                "rnd": 0,
                "sample": 0,
                "trial": 0,
                "repair": 0,
                "dept_procurement": 0,
            }
        field = status_field_map.get(status)
        if field:
            summary[sku_id][field] = cnt
    for sku_id, condition, cnt in in_stock_rows:
        if sku_id not in summary:
            continue
        detail_field = (condition or StockCondition.NEW.value).lower()
        details = summary[sku_id]["in_stock_details"]
        if detail_field in details:
            details[detail_field] = cnt
    return list(summary.values())


def get_stock_summary_by_partner(db: Session, sku_ids: list[int] | None = None) -> list[dict]:
    """按关联单位汇总不在库单品各状态数量。

    不在库的单品通过 last_order_no 关联到出/入库单，再解析到往来单位。
    """
    query = (
        db.query(
            InventoryItem.last_order_no,
            InventoryItem.stock_status,
            func.count(InventoryItem.id).label("cnt"),
        )
        .filter(InventoryItem.stock_status != StockStatus.IN_STOCK.value)
    )
    if sku_ids:
        query = query.filter(InventoryItem.sku_id.in_(sku_ids))
    rows = query.group_by(InventoryItem.last_order_no, InventoryItem.stock_status).all()

    order_nos = {order_no for order_no, _, _ in rows if order_no}
    inbound_nos = {no for no in order_nos if no.startswith("JIN-")}
    outbound_nos = order_nos - inbound_nos
    inbound_map = _partner_map(db, InboundOrder, inbound_nos)
    outbound_map = _partner_map(db, OutboundOrder, outbound_nos)

    status_field_map = {
        StockStatus.SOLD.value: "sold",
        StockStatus.PRESOLD.value: "presold",
        StockStatus.SOLD_OFFLINE.value: "sold_offline",
        StockStatus.BORROWED.value: "borrowed",
        StockStatus.GIFTED.value: "gifted",
        StockStatus.SCRAPPED.value: "scrapped",
        StockStatus.RND.value: "rnd",
        StockStatus.SAMPLE.value: "sample",
        StockStatus.TRIAL.value: "trial",
        StockStatus.REPAIR.value: "repair",
        StockStatus.DEPT_PROCUREMENT.value: "dept_procurement",
    }

    summary: dict = {}
    for order_no, status, cnt in rows:
        field = status_field_map.get(status)
        if not field:
            continue
        partner_info = _resolve_partner_from_order_no(order_no, inbound_map, outbound_map)
        partner_id = partner_info.get("partner_id")
        key = partner_id if partner_id is not None else "__unknown__"
        if key not in summary:
            summary[key] = {
                "partner_id": partner_id,
                "partner_name": partner_info.get("partner_name") or "未知单位",
                "partner_group_name": partner_info.get("partner_group_name"),
                "sold": 0,
                "presold": 0,
                "sold_offline": 0,
                "borrowed": 0,
                "gifted": 0,
                "scrapped": 0,
                "rnd": 0,
                "sample": 0,
                "trial": 0,
                "repair": 0,
                "dept_procurement": 0,
            }
        summary[key][field] += cnt

    return sorted(summary.values(), key=lambda x: (x["partner_id"] is None, x["partner_name"]))


def complete_offline_sale(db: Session, item: InventoryItem, user_id: int) -> InventoryItem:
    """确认线下销售完成：准售出 → 售出-线下。"""
    if item.stock_status != StockStatus.PRESOLD.value:
        raise ValueError("仅准售出状态的单品可确认线下成交")
    if item.operation_status != OperationStatus.COMPLETED.value:
        raise ValueError("单品正在被其他单据处理中")
    old_stock = item.stock_status
    item.stock_status = StockStatus.SOLD_OFFLINE.value
    record_history(
        db,
        item,
        "STATUS_CHANGE",
        None,
        user_id,
        from_stock=old_stock,
        to_stock=StockStatus.SOLD_OFFLINE.value,
        remark="确认线下销售完成",
    )
    db.commit()
    db.refresh(item)
    return item
