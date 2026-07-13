from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogCreate
from app.schemas.common import R, PageResult
from app.schemas.inventory import InventoryItemResponse, InventoryHistoryResponse
from app.service import audit_service, inventory_service
from app.utils.request_ip import get_client_ip

router = APIRouter(prefix="/inventory/items", tags=["库存"])


@router.get("", response_model=R[PageResult[InventoryItemResponse]], summary="库存单品列表")
def list_items(
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
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total, items = inventory_service.get_items(
        db,
        page,
        page_size,
        item_sn,
        sku_id,
        stock_status,
        stock_condition,
        operation_status,
        last_order_no,
        category_id,
        keyword,
    )
    return R.ok(data=PageResult(total=total, page=page, page_size=page_size,
                                items=[InventoryItemResponse(**i) for i in items]))


@router.get("/available", response_model=R[PageResult[InventoryItemResponse]], summary="可出库单品")
def available_items(
    page: int = 1,
    page_size: int = 50,
    sku_id: int | None = None,
    item_sn: str | None = None,
    stock_condition: str | None = None,
    keyword: str | None = None,
    category_id: int | None = None,
    outbound_order_id: int | None = Query(None, description="编辑出库单时传入，以包含本单已锁定单品"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        total, items = inventory_service.get_available_items(
            db,
            sku_id,
            item_sn,
            stock_condition,
            keyword,
            category_id,
            page,
            page_size,
            outbound_order_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return R.ok(data=PageResult(total=total, page=page, page_size=page_size,
                                items=[InventoryItemResponse(**i) for i in items]))


@router.get("/export", summary="导出库存明细 Excel")
def export_items(
    request: Request,
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = inventory_service.export_items_xlsx(
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
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="EXPORT",
            module="inventory",
            resource_type="inventory_export",
            summary=audit_service.build_summary(user, "EXPORT", "库存明细 Excel"),
            after_data={
                "filters": {
                    "item_sn": item_sn,
                    "sku_id": sku_id,
                    "stock_status": stock_status,
                    "stock_condition": stock_condition,
                    "operation_status": operation_status,
                    "last_order_no": last_order_no,
                    "category_id": category_id,
                    "keyword": keyword,
                }
            },
            ip_address=get_client_ip(request),
        ),
    )
    filename = quote(f"IMS-实时库存-{datetime.now().strftime('%Y%m%d')}.xlsx")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/{item_sn}", response_model=R[InventoryItemResponse], summary="单品详情")
def get_item(item_sn: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = inventory_service.get_item_by_sn(db, item_sn)
    if not item:
        raise HTTPException(status_code=404, detail="单品不存在")
    return R.ok(data=InventoryItemResponse(**inventory_service.get_item_detail(db, item)))


@router.get("/{item_sn}/history", response_model=R[list[InventoryHistoryResponse]], summary="变动轨迹")
def item_history(item_sn: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = inventory_service.get_item_by_sn(db, item_sn)
    if not item:
        raise HTTPException(status_code=404, detail="单品不存在")
    history = inventory_service.get_item_history(db, item.id)
    return R.ok(data=[InventoryHistoryResponse.model_validate(h) for h in history])


@router.post("/{item_sn}/complete-offline-sale", response_model=R[InventoryItemResponse], summary="确认线下销售完成")
def complete_offline_sale(
    item_sn: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = inventory_service.get_item_by_sn(db, item_sn)
    if not item:
        raise HTTPException(status_code=404, detail="单品不存在")
    try:
        item = inventory_service.complete_offline_sale(db, item, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    detail = inventory_service.get_item_detail(db, item)
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="UPDATE",
            module="inventory",
            resource_type="inventory_item",
            resource_id=str(item.id),
            summary=audit_service.build_summary(user, "UPDATE", f"确认线下销售完成 [{item_sn}]"),
            after_data={"item_sn": item_sn, "stock_status": item.stock_status},
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=InventoryItemResponse(**detail))
