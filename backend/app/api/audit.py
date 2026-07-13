from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.common import R, PageResult
from app.service import audit_service

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


@router.get("", response_model=R[PageResult[AuditLogResponse]], summary="审计日志列表")
def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    operator_id: int | None = None,
    operator_keyword: str | None = None,
    module: str | None = None,
    action: str | None = None,
    keyword: str | None = None,
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """分页查询系统审计日志，仅管理员可访问。"""
    total, items = audit_service.get_logs(
        db,
        page=page,
        page_size=page_size,
        operator_id=operator_id,
        operator_keyword=operator_keyword,
        module=module,
        action=action,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
    )
    return R.ok(
        data=PageResult(
            total=total,
            page=page,
            page_size=page_size,
            items=[AuditLogResponse.model_validate(i) for i in items],
        )
    )
