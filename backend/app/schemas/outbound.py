from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.enums import OutboundType


class OutboundOrderCreate(BaseModel):
    order_no: str | None = None
    outbound_type: OutboundType
    partner_id: int = Field(..., description="关联往来单位")
    customer_name: str = Field(..., max_length=200, description="客户名称")
    remark: str | None = None
    item_ids: list[int] = Field(..., min_length=1)

    @field_validator("customer_name")
    @classmethod
    def customer_name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("客户名称不能为空")
        return v


class OutboundOrderUpdate(BaseModel):
    outbound_type: OutboundType | None = None
    partner_id: int | None = None
    customer_name: str | None = None
    remark: str | None = None
    item_ids: list[int] | None = None

    @field_validator("customer_name")
    @classmethod
    def customer_name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("客户名称不能为空")
        return v


class OutboundOrderItemResponse(BaseModel):
    id: int
    item_id: int
    sku_id: int
    quantity: int
    item_sn: str | None = None
    sku_name: str | None = None
    sku_unit: str | None = None
    barcode: str | None = None
    category_name: str | None = None
    stock_status: str | None = None
    stock_condition: str | None = None
    operation_status: str | None = None
    model_config = {"from_attributes": True}


class OutboundOrderResponse(BaseModel):
    id: int
    order_no: str
    outbound_type: str
    partner_id: int
    partner_name: str | None = None
    partner_group_id: int | None = None
    partner_group_name: str | None = None
    customer_name: str | None = None
    remark: str | None
    operation_status: str
    total_qty: int
    submitted_by: int | None
    reviewed_by: int | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[OutboundOrderItemResponse] = []
    model_config = {"from_attributes": True}
