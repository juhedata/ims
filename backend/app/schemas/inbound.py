from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.enums import InboundMode, StockCondition


class InboundLineCreate(BaseModel):
    sku_id: int
    quantity: int = Field(..., ge=1)
    unit_price: Decimal | None = Field(None, ge=0, le=99999.99, max_digits=12, decimal_places=2, description="采购单价")
    item_sns: list[str] | None = Field(None, description="人工录入 SN 列表，数量须与 quantity 一致")


class InboundOrderCreate(BaseModel):
    order_no: str | None = None
    inbound_mode: InboundMode
    stock_condition: StockCondition
    partner_id: int = Field(..., description="关联往来单位")
    related_outbound_order_id: int | None = None
    remark: str | None = None
    lines: list[InboundLineCreate] | None = None
    return_item_ids: list[int] | None = Field(
        None, description="非采购入库时勾选的退货单品 ID（支持部分退货）"
    )


class InboundOrderUpdate(BaseModel):
    stock_condition: StockCondition | None = None
    partner_id: int | None = None
    related_outbound_order_id: int | None = None
    remark: str | None = None
    lines: list[InboundLineCreate] | None = None
    return_item_ids: list[int] | None = Field(
        None, description="非采购入库时勾选的退货单品 ID"
    )


class ReturnableItemResponse(BaseModel):
    """关联出库单中可退货的单品。"""
    item_id: int
    item_sn: str
    sku_id: int
    sku_name: str
    stock_status: str
    stock_condition: str | None = None


class InboundOrderItemResponse(BaseModel):
    id: int
    item_sn: str
    item_id: int | None
    sn_source: str
    line_id: int
    sku_id: int | None = None
    sku_name: str | None = None
    sku_unit: str | None = None
    unit_price: Decimal | None = None
    model_config = {"from_attributes": True}


class InboundOrderLineResponse(BaseModel):
    id: int
    sku_id: int
    quantity: int
    unit_price: Decimal | None = None
    model_config = {"from_attributes": True}


class InboundOrderResponse(BaseModel):
    id: int
    order_no: str
    inbound_mode: str
    stock_condition: str
    partner_id: int
    partner_name: str | None = None
    partner_group_id: int | None = None
    partner_group_name: str | None = None
    related_outbound_order_id: int | None
    remark: str | None
    operation_status: str
    total_qty: int
    submitted_by: int | None
    reviewed_by: int | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lines: list[InboundOrderLineResponse] = []
    items: list[InboundOrderItemResponse] = []
    model_config = {"from_attributes": True}


class SnValidateRequest(BaseModel):
    sns: list[str]
    exclude_order_id: int | None = None
