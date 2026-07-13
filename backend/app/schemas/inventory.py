from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.enums import RETURN_CONDITION_ORDER, StockCondition


def _in_stock_detail_field(condition: str) -> str:
    return (condition or StockCondition.NEW.value).lower()


IN_STOCK_DETAIL_FIELDS = [_in_stock_detail_field(c.value) for c in [StockCondition.NEW, *RETURN_CONDITION_ORDER]]


class InStockDetails(BaseModel):
    new: int = 0
    returned_from_sale: int = 0
    returned_from_sold_offline: int = 0
    returned_from_presold: int = 0
    returned_from_borrow: int = 0
    returned_from_gift: int = 0
    returned_from_scrapped: int = 0
    returned_from_rnd: int = 0
    returned_from_sample: int = 0
    returned_from_trial: int = 0
    returned_from_repair: int = 0
    returned_from_dept_procurement: int = 0


def empty_in_stock_details() -> dict[str, int]:
    return {field: 0 for field in IN_STOCK_DETAIL_FIELDS}


class InventoryItemResponse(BaseModel):
    id: int
    item_sn: str
    sku_id: int
    sku_name: str | None = None
    stock_status: str
    stock_condition: str
    operation_status: str
    last_order_no: str | None
    unit_price: Decimal | None = None
    quantity: int
    partner_id: int | None = None
    partner_name: str | None = None
    partner_group_id: int | None = None
    partner_group_name: str | None = None
    customer_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InventoryHistoryResponse(BaseModel):
    id: int
    item_id: int
    event_type: str
    order_no: str | None
    from_stock_status: str | None
    to_stock_status: str | None
    from_operation_status: str | None
    to_operation_status: str | None
    operator_id: int | None
    remark: str | None
    created_at: datetime
    partner_id: int | None = None
    partner_name: str | None = None
    partner_group_id: int | None = None
    partner_group_name: str | None = None
    model_config = {"from_attributes": True}


class StockSummaryItem(BaseModel):
    sku_id: int
    sku_name: str
    in_stock: int = 0
    in_stock_details: InStockDetails = Field(default_factory=InStockDetails)
    sold: int = 0
    presold: int = 0
    sold_offline: int = 0
    borrowed: int = 0
    gifted: int = 0
    scrapped: int = 0
    rnd: int = 0
    sample: int = 0
    trial: int = 0
    repair: int = 0
    dept_procurement: int = 0
