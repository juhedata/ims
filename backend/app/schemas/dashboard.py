from pydantic import BaseModel
from app.schemas.inventory import StockSummaryItem


class PendingAuditResponse(BaseModel):
    inbound_pending: int
    outbound_pending: int


class DashboardStockSummary(BaseModel):
    items: list[StockSummaryItem]


class PartnerStockSummaryItem(BaseModel):
    partner_id: int | None = None
    partner_name: str
    partner_group_name: str | None = None
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


class DashboardPartnerSummary(BaseModel):
    items: list[PartnerStockSummaryItem]
