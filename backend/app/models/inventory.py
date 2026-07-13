from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import OperationStatus, StockCondition, StockStatus


class InventoryItem(Base, TimestampMixin):
    """库存单品（一物一码核心表）。"""

    __tablename__ = "inventory_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_sn: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="Item SN")
    sku_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_sku.id"), nullable=False, index=True, comment="SKU ID"
    )
    stock_status: Mapped[str] = mapped_column(
        String(30), default=StockStatus.IN_STOCK.value, nullable=False, index=True, comment="库存状态"
    )
    stock_condition: Mapped[str] = mapped_column(
        String(30), default=StockCondition.NEW.value, nullable=False, comment="库存属性"
    )
    operation_status: Mapped[str] = mapped_column(
        String(30), default=OperationStatus.COMPLETED.value, nullable=False, comment="操作状态"
    )
    last_order_no: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="最近关联单号")
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, comment="采购单价")
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="数量，固定为1")


class InventoryItemHistory(Base):
    """单品变动轨迹。"""

    __tablename__ = "inventory_item_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_item.id"), nullable=False, index=True, comment="单品ID"
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="INBOUND/OUTBOUND/STATUS_CHANGE")
    order_no: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="关联单号")
    from_stock_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_stock_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    from_operation_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_operation_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="记录时间")


class InventoryItemSnapshot(Base):
    """库存单品快照（日快照 / 月快照）。"""

    __tablename__ = "inventory_item_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, comment="快照时间")
    snapshot_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True, comment="快照业务日期")
    snapshot_type: Mapped[str] = mapped_column(
        String(10), default="DAILY", nullable=False, index=True, comment="DAILY/MONTHLY"
    )
    snapshot_month: Mapped[str | None] = mapped_column(
        String(7), nullable=True, index=True, comment="快照所属月份，格式 YYYY-MM"
    )
    item_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="原单品ID")
    item_sn: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sku_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_status: Mapped[str] = mapped_column(String(30), nullable=False)
    stock_condition: Mapped[str] = mapped_column(String(30), nullable=False)
    operation_status: Mapped[str] = mapped_column(String(30), nullable=False)
    last_order_no: Mapped[str | None] = mapped_column(String(30), nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, comment="采购单价")
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class InventoryDailySummary(Base):
    """库存日汇总（财务流水：期初/期末在库数量与资产金额）。"""

    __tablename__ = "inventory_daily_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True, comment="业务日期")
    opening_in_stock_qty: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="期初在库件数")
    inbound_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="当日审核入库件数")
    outbound_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="当日审核出库件数")
    closing_in_stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="期末在库件数")
    closing_asset_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True, comment="期末在库资产金额"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class InventorySkuDailyLedger(Base):
    """SKU 日流水（快照任务预生成，库存流水直接读库）。"""

    __tablename__ = "inventory_sku_daily_ledger"

    snapshot_date: Mapped[date] = mapped_column(Date, primary_key=True, comment="业务日期")
    sku_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_sku.id"), primary_key=True, index=True, comment="SKU ID"
    )
    opening_in_stock_qty: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="期初在库件数")
    inbound_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="当日审核入库件数")
    outbound_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="当日审核出库件数")
    # 入库按类型件数
    inbound_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-正常")
    inbound_returned_from_sale: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-线上售出退回")
    inbound_returned_from_sold_offline: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-线下售出退回")
    inbound_returned_from_presold: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-准售出退回")
    inbound_returned_from_gift: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-赠送退回")
    inbound_returned_from_scrapped: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-损毁退回")
    inbound_returned_from_rnd: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-研发退回")
    inbound_returned_from_sample: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-样机退回")
    inbound_returned_from_trial: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-试用退回")
    inbound_returned_from_repair: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-维修退回")
    inbound_returned_from_dept_procurement: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="入库-部门采购退回")
    # 出库按类型件数
    outbound_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-售出-线上")
    outbound_sold_offline: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-售出-线下")
    outbound_presold: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-准售出")
    outbound_gifted: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-赠送")
    outbound_scrapped: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-损毁")
    outbound_rnd: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-研发")
    outbound_sample: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-样机")
    outbound_trial: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-试用")
    outbound_repair: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-维修")
    outbound_dept_procurement: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-部门采购")
    outbound_borrowed: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="出库-借用")
    closing_in_stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="期末在库件数")
    closing_asset_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True, comment="期末在库资产金额"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
