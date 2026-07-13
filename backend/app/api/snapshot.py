from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import R, PageResult
from app.schemas.snapshot import (
    DailyLedgerBreakdownResponse,
    DailyLedgerBreakdownItem,
    DailyLedgerResponse,
    LedgerPeriodSkuBreakdownResponse,
    LedgerPeriodSkuSummaryResponse,
    SnapshotBatchResponse,
    SnapshotItemResponse,
)
from app.service import snapshot_service

router = APIRouter(prefix="/snapshots", tags=["库存快照"])


def _parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{field_name} 格式应为 YYYY-MM-DD") from exc


def _item_filter_params(
    item_sn: str | None = None,
    sku_id: int | None = None,
    stock_status: str | None = None,
    stock_condition: str | None = None,
    operation_status: str | None = None,
    last_order_no: str | None = None,
    category_id: int | None = None,
    keyword: str | None = None,
) -> dict:
    return {
        "item_sn": item_sn,
        "sku_id": sku_id,
        "stock_status": stock_status,
        "stock_condition": stock_condition,
        "operation_status": operation_status,
        "last_order_no": last_order_no,
        "category_id": category_id,
        "keyword": keyword,
    }


@router.get("", response_model=R[list[SnapshotBatchResponse]], summary="快照批次列表")
def list_snapshots(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    batches = snapshot_service.list_snapshots(db)
    return R.ok(data=[SnapshotBatchResponse(**b) for b in batches])


@router.get("/dates", response_model=R[list[str]], summary="快照日期列表")
def snapshot_dates(
    date_from: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_from = _parse_date(date_from, "date_from") if date_from else None
    parsed_to = _parse_date(date_to, "date_to") if date_to else None
    return R.ok(data=snapshot_service.list_snapshot_dates(db, parsed_from, parsed_to))


@router.get("/daily-ledger", response_model=R[list[DailyLedgerResponse]], summary="库存日流水")
def daily_ledger(
    date_from: str = Query(..., description="开始日期 YYYY-MM-DD"),
    date_to: str = Query(..., description="结束日期 YYYY-MM-DD"),
    sku_id: int | None = Query(None, description="指定 SKU"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_from = _parse_date(date_from, "date_from")
    parsed_to = _parse_date(date_to, "date_to")
    if parsed_from > parsed_to:
        raise HTTPException(status_code=400, detail="date_from 不能晚于 date_to")
    rows = snapshot_service.get_daily_ledger(db, parsed_from, parsed_to, sku_id=sku_id)
    return R.ok(data=[DailyLedgerResponse(**row) for row in rows])


@router.get(
    "/daily-ledger/{snapshot_date}/breakdown",
    response_model=R[DailyLedgerBreakdownResponse],
    summary="库存日流水明细（按 SKU / 库存属性）",
)
def daily_ledger_breakdown(
    snapshot_date: str,
    dimension: str = Query(..., description="sku | stock_condition"),
    sku_id: int | None = Query(None, description="指定 SKU 时按库存属性汇总"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_date = _parse_date(snapshot_date, "snapshot_date")
    try:
        items = snapshot_service.get_daily_ledger_breakdown(db, parsed_date, dimension, sku_id=sku_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return R.ok(
        data=DailyLedgerBreakdownResponse(
            snapshot_date=snapshot_date,
            dimension=dimension,
            sku_id=sku_id,
            items=[DailyLedgerBreakdownItem(**item) for item in items],
        )
    )


@router.get("/daily-ledger/export", summary="导出库存日流水 Excel")
def export_daily_ledger(
    date_from: str = Query(..., description="开始日期 YYYY-MM-DD"),
    date_to: str = Query(..., description="结束日期 YYYY-MM-DD"),
    sku_id: int | None = Query(None, description="指定 SKU"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_from = _parse_date(date_from, "date_from")
    parsed_to = _parse_date(date_to, "date_to")
    if parsed_from > parsed_to:
        raise HTTPException(status_code=400, detail="date_from 不能晚于 date_to")
    content = snapshot_service.export_daily_ledger_xlsx(db, parsed_from, parsed_to, sku_id=sku_id)
    filename = quote(f"库存日流水_{date_from}_{date_to}.xlsx")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/ledger-summary",
    response_model=R[list[LedgerPeriodSkuSummaryResponse]],
    summary="库存快照汇总（按 SKU）",
)
def ledger_period_sku_summary(
    date_from: str = Query(..., description="开始日期 YYYY-MM-DD"),
    date_to: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_from = _parse_date(date_from, "date_from")
    parsed_to = _parse_date(date_to, "date_to")
    if parsed_from > parsed_to:
        raise HTTPException(status_code=400, detail="date_from 不能晚于 date_to")
    rows = snapshot_service.get_ledger_period_sku_summary(db, parsed_from, parsed_to)
    return R.ok(data=[LedgerPeriodSkuSummaryResponse(**row) for row in rows])


@router.get(
    "/ledger-summary/{sku_id}/breakdown",
    response_model=R[LedgerPeriodSkuBreakdownResponse],
    summary="库存快照汇总明细（某 SKU 按库存属性）",
)
def ledger_period_sku_breakdown(
    sku_id: int,
    date_from: str = Query(..., description="开始日期 YYYY-MM-DD"),
    date_to: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_from = _parse_date(date_from, "date_from")
    parsed_to = _parse_date(date_to, "date_to")
    if parsed_from > parsed_to:
        raise HTTPException(status_code=400, detail="date_from 不能晚于 date_to")
    items = snapshot_service.get_ledger_period_sku_condition_breakdown(
        db, parsed_from, parsed_to, sku_id
    )
    sku_name = str(sku_id)
    for row in snapshot_service.get_ledger_period_sku_summary(db, parsed_from, parsed_to):
        if row["sku_id"] == sku_id:
            sku_name = row["sku_name"]
            break
    return R.ok(
        data=LedgerPeriodSkuBreakdownResponse(
            sku_id=sku_id,
            sku_name=sku_name,
            date_from=date_from,
            date_to=date_to,
            items=[DailyLedgerBreakdownItem(**item) for item in items],
        )
    )


@router.get("/ledger-summary/export", summary="导出库存快照汇总 Excel")
def export_ledger_period_summary(
    date_from: str = Query(..., description="开始日期 YYYY-MM-DD"),
    date_to: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parsed_from = _parse_date(date_from, "date_from")
    parsed_to = _parse_date(date_to, "date_to")
    if parsed_from > parsed_to:
        raise HTTPException(status_code=400, detail="date_from 不能晚于 date_to")
    content = snapshot_service.export_ledger_period_sku_summary_xlsx(db, parsed_from, parsed_to)
    filename = quote(f"库存快照汇总_{date_from}_{date_to}.xlsx")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/items", response_model=R[PageResult[SnapshotItemResponse]], summary="快照明细")
def snapshot_items(
    snapshot_date: str = Query(..., description="快照日期 YYYY-MM-DD"),
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
    filters = _item_filter_params(
        item_sn=item_sn,
        sku_id=sku_id,
        stock_status=stock_status,
        stock_condition=stock_condition,
        operation_status=operation_status,
        last_order_no=last_order_no,
        category_id=category_id,
        keyword=keyword,
    )
    parsed_date = _parse_date(snapshot_date, "snapshot_date")
    total, items = snapshot_service.get_snapshot_items_by_date(
        db, parsed_date, page, page_size, **filters
    )
    return R.ok(
        data=PageResult(
            total=total,
            page=page,
            page_size=page_size,
            items=[SnapshotItemResponse.model_validate(i) for i in items],
        )
    )


@router.get("/items/export", summary="导出快照明细 Excel")
def export_snapshot_items(
    snapshot_date: str = Query(..., description="快照日期 YYYY-MM-DD"),
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
    filters = _item_filter_params(
        item_sn=item_sn,
        sku_id=sku_id,
        stock_status=stock_status,
        stock_condition=stock_condition,
        operation_status=operation_status,
        last_order_no=last_order_no,
        category_id=category_id,
        keyword=keyword,
    )
    parsed_date = _parse_date(snapshot_date, "snapshot_date")
    content = snapshot_service.export_snapshot_items_xlsx(db, snapshot_date=parsed_date, **filters)
    filename = quote(f"库存快照明细_{snapshot_date}.xlsx")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/trigger", response_model=R, summary="手动触发日快照")
def trigger_snapshot(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = snapshot_service.create_daily_snapshot(db)
    return R.ok(data=result, msg="日快照完成")
