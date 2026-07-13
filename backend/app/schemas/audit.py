from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """审计日志列表项。"""

    id: int
    operator_id: int | None
    operator_name: str
    action: str
    module: str
    resource_type: str | None
    resource_id: str | None
    resource_name: str | None
    summary: str
    before_data: str | None
    after_data: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogCreate(BaseModel):
    """内部写入审计日志的请求体（service 层使用）。"""

    action: str
    module: str
    summary: str
    resource_type: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None
    before_data: dict | list | str | None = None
    after_data: dict | list | str | None = None
    ip_address: str | None = None
