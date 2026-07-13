from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogCreate
from app.schemas.common import R, PageResult
from app.schemas.inbound import *
from app.service import audit_service, inbound_service
from app.utils.order_no import generate_inbound_no
from app.utils.request_ip import get_client_ip
from app.utils.sn_generator import validate_sn_unique

router = APIRouter(prefix="/inbound/orders", tags=["入库"])


def _order_audit_data(order) -> dict:
    """将入库单转为审计快照。"""
    return audit_service.to_audit_data(InboundOrderResponse.model_validate(order))


@router.get("/generate-no", response_model=R[str], summary="生成入库单号")
def gen_no(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return R.ok(data=generate_inbound_no(db))


@router.post("/validate-sns", response_model=R[list[str]], summary="SN唯一性校验")
def validate_sns(req: SnValidateRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    dup = validate_sn_unique(db, req.sns, req.exclude_order_id)
    return R.ok(data=dup, msg="校验完成" if not dup else "存在重复SN")


@router.get("/returnable-items", response_model=R[PageResult[ReturnableItemResponse]], summary="可退货单品列表")
def returnable_items(
    outbound_order_id: int,
    stock_condition: str,
    exclude_inbound_order_id: int | None = None,
    keyword: str | None = None,
    sku_id: int | None = None,
    category_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        total, items = inbound_service.get_returnable_items(
            db,
            outbound_order_id,
            stock_condition,
            exclude_inbound_order_id,
            keyword,
            sku_id,
            category_id,
            page,
            page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return R.ok(data=PageResult(
        total=total,
        page=page,
        page_size=page_size,
        items=[ReturnableItemResponse(**i) for i in items],
    ))


@router.get("", response_model=R[PageResult[InboundOrderResponse]], summary="入库单列表")
def list_orders(
    page: int = 1,
    page_size: int = 20,
    operation_status: str | None = None,
    inbound_mode: str | None = None,
    order_no: str | None = None,
    partner_id: int | None = None,
    stock_condition: str | None = None,
    sku_id: int | None = Query(None, description="商品 SKU ID"),
    start_time: datetime | None = Query(None, description="创建时间起"),
    end_time: datetime | None = Query(None, description="创建时间止"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total, items = inbound_service.get_orders(
        db, page, page_size, operation_status, inbound_mode, order_no, partner_id, stock_condition,
        sku_id, start_time, end_time,
    )
    return R.ok(data=PageResult(total=total, page=page, page_size=page_size,
                                items=[InboundOrderResponse.model_validate(o) for o in items]))


@router.post("", response_model=R[InboundOrderResponse], status_code=201, summary="新建入库单")
def create_order(
    data: InboundOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        order = inbound_service.create_order(db, data, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    order = inbound_service.get_order_detail(db, order.id)
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="CREATE",
            module="inbound",
            resource_type="inbound_order",
            resource_id=str(order.id),
            resource_name=order.order_no,
            summary=audit_service.build_summary(user, "CREATE", f"入库单「{order.order_no}」"),
            after_data=_order_audit_data(order),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=InboundOrderResponse.model_validate(order))


@router.get("/{order_id}", response_model=R[InboundOrderResponse], summary="入库单详情")
def get_order(
    order_id: str,
    lookup_by: str = "id",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if lookup_by == "order_no":
        key = order_id
    elif lookup_by == "id":
        if not order_id.isdigit():
            raise HTTPException(status_code=400, detail="lookup_by=id 时 order_id 必须为整数")
        key = int(order_id)
    else:
        raise HTTPException(status_code=400, detail="lookup_by 仅支持 'id' 或 'order_no'")
    order = inbound_service.get_order_detail(db, key)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    return R.ok(data=InboundOrderResponse.model_validate(order))


@router.put("/{order_id}", response_model=R[InboundOrderResponse], summary="修改入库单")
def update_order(
    order_id: int,
    data: InboundOrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = inbound_service.get_order_detail(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    before = _order_audit_data(order)
    try:
        order = inbound_service.update_order(db, order, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    order = inbound_service.get_order_detail(db, order.id)
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="UPDATE",
            module="inbound",
            resource_type="inbound_order",
            resource_id=str(order.id),
            resource_name=order.order_no,
            summary=audit_service.build_summary(user, "UPDATE", f"入库单「{order.order_no}」"),
            before_data=before,
            after_data=_order_audit_data(order),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=InboundOrderResponse.model_validate(order))


@router.post("/{order_id}/submit", response_model=R[InboundOrderResponse], summary="提交待审核")
def submit_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = inbound_service.get_order_detail(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    before_status = order.operation_status
    try:
        order = inbound_service.submit_order(db, order, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="SUBMIT",
            module="inbound",
            resource_type="inbound_order",
            resource_id=str(order.id),
            resource_name=order.order_no,
            summary=audit_service.build_summary(
                user, "SUBMIT", f"入库单「{order.order_no}」", f"状态 {before_status} → {order.operation_status}"
            ),
            before_data={"operation_status": before_status},
            after_data={"operation_status": order.operation_status},
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=InboundOrderResponse.model_validate(order), msg="提交成功")


@router.post("/{order_id}/approve", response_model=R[InboundOrderResponse], summary="审核通过")
def approve_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = inbound_service.get_order_detail(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    before = _order_audit_data(order)
    try:
        order = inbound_service.approve_order(db, order, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    order = inbound_service.get_order_detail(db, order.id)
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="APPROVE",
            module="inbound",
            resource_type="inbound_order",
            resource_id=str(order.id),
            resource_name=order.order_no,
            summary=audit_service.build_summary(user, "APPROVE", f"入库单「{order.order_no}」"),
            before_data=before,
            after_data=_order_audit_data(order),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=InboundOrderResponse.model_validate(order), msg="审核通过")


@router.post("/{order_id}/cancel", response_model=R[InboundOrderResponse], summary="取消")
def cancel_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = inbound_service.get_order_detail(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    before_status = order.operation_status
    try:
        order = inbound_service.cancel_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="CANCEL",
            module="inbound",
            resource_type="inbound_order",
            resource_id=str(order.id),
            resource_name=order.order_no,
            summary=audit_service.build_summary(
                user, "CANCEL", f"入库单「{order.order_no}」", f"状态 {before_status} → {order.operation_status}"
            ),
            before_data={"operation_status": before_status},
            after_data={"operation_status": order.operation_status},
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=InboundOrderResponse.model_validate(order), msg="已取消")


@router.delete("/{order_id}", response_model=R, summary="删除入库单")
def delete_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = inbound_service.get_order_detail(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    before = _order_audit_data(order)
    order_no = order.order_no
    try:
        inbound_service.delete_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="DELETE",
            module="inbound",
            resource_type="inbound_order",
            resource_id=str(order_id),
            resource_name=order_no,
            summary=audit_service.build_summary(user, "DELETE", f"入库单「{order_no}」"),
            before_data=before,
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(msg="删除成功")
