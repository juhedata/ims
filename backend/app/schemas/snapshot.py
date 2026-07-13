from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class SnapshotBatchResponse(BaseModel):
    snapshot_at: datetime
    snapshot_type: str | None = None
    item_count: int


class DailyLedgerResponse(BaseModel):
    snapshot_date: str
    sku_id: int | None = None
    sku_name: str | None = None
    opening_in_stock_qty: int | None = None
    inbound_qty: int
    outbound_qty: int
    inbound_by_type: dict[str, int] = {}
    outbound_by_type: dict[str, int] = {}
    closing_in_stock_qty: int
    closing_asset_amount: Decimal | None = None


class DailyLedgerBreakdownItem(BaseModel):
    dimension_key: str
    dimension_label: str
    opening_in_stock_qty: int | None = None
    inbound_qty: int = 0
    outbound_qty: int = 0
    closing_in_stock_qty: int = 0
    closing_asset_amount: Decimal | None = None
    expected_closing_qty: int | None = None
    balanced: bool | None = None
    diff_qty: int | None = None


class DailyLedgerBreakdownResponse(BaseModel):
    snapshot_date: str
    dimension: str
    sku_id: int | None = None
    items: list[DailyLedgerBreakdownItem]


class LedgerPeriodSkuSummaryResponse(BaseModel):
    sku_id: int
    sku_name: str
    date_from: str
    date_to: str
    opening_in_stock_qty: int | None = None
    total_inbound_qty: int
    total_outbound_qty: int
    inbound_by_type: dict[str, int] = {}
    outbound_by_type: dict[str, int] = {}
    expected_closing_qty: int | None = None
    closing_in_stock_qty: int
    closing_asset_amount: Decimal | None = None
    balanced: bool
    diff_qty: int | None = None


class LedgerPeriodSkuBreakdownResponse(BaseModel):
    sku_id: int
    sku_name: str
    date_from: str
    date_to: str
    items: list[DailyLedgerBreakdownItem]


class SnapshotItemResponse(BaseModel):
    id: int
    snapshot_at: datetime
    snapshot_date: date | None = None
    snapshot_type: str | None = None
    snapshot_month: str | None = None
    item_id: int
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
    model_config = {"from_attributes": True}
