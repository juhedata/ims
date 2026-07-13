from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import InboundMode, OperationStatus
from app.models.partner import Partner
from app.models.product import ProductSku


class InboundOrder(Base, TimestampMixin):
    """入库单。"""

    __tablename__ = "inbound_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True, comment="JIN-单号")
    inbound_mode: Mapped[str] = mapped_column(String(20), nullable=False, comment="PROCUREMENT/NON_PROCUREMENT")
    stock_condition: Mapped[str] = mapped_column(String(30), nullable=False, comment="入库类型/库存属性")
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("partner.id"), nullable=False, comment="往来单位")
    related_outbound_order_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("outbound_order.id"), nullable=True, comment="关联出库单（非采购入库）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    operation_status: Mapped[str] = mapped_column(
        String(30), default=OperationStatus.INITIATED.value, nullable=False, index=True
    )
    total_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="商品总数量")
    submitted_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lines: Mapped[list["InboundOrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    items: Mapped[list["InboundOrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    partner: Mapped["Partner"] = relationship(foreign_keys=[partner_id], lazy="select")

    @property
    def partner_name(self) -> str | None:
        return self.partner.name if self.partner else None

    @property
    def partner_group_id(self) -> int | None:
        return self.partner.group_id if self.partner else None

    @property
    def partner_group_name(self) -> str | None:
        return self.partner.group.name if self.partner and self.partner.group else None


class InboundOrderLine(Base):
    """入库单商品行。"""

    __tablename__ = "inbound_order_line"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inbound_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inbound_order.id"), nullable=False, index=True
    )
    sku_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_sku.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="商品数量")
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, comment="采购单价")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    order: Mapped["InboundOrder"] = relationship(back_populates="lines")
    items: Mapped[list["InboundOrderItem"]] = relationship(back_populates="line")
    sku: Mapped["ProductSku"] = relationship(foreign_keys=[sku_id], lazy="select")


class InboundOrderItem(Base):
    """入库单单品绑定（SN）。"""

    __tablename__ = "inbound_order_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inbound_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inbound_order.id"), nullable=False, index=True
    )
    line_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inbound_order_line.id"), nullable=False)
    item_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("inventory_item.id"), nullable=True)
    item_sn: Mapped[str] = mapped_column(String(50), nullable=False, comment="录入或生成的SN")
    sn_source: Mapped[str] = mapped_column(String(10), default="MANUAL", nullable=False, comment="MANUAL/AUTO")

    order: Mapped["InboundOrder"] = relationship(back_populates="items")
    line: Mapped["InboundOrderLine"] = relationship(back_populates="items")

    @property
    def sku_id(self) -> int | None:
        return self.line.sku_id if self.line else None

    @property
    def sku_name(self) -> str | None:
        return self.line.sku.name if self.line and self.line.sku else None

    @property
    def sku_unit(self) -> str | None:
        return self.line.sku.unit if self.line and self.line.sku else None

    @property
    def unit_price(self) -> Decimal | None:
        return self.line.unit_price if self.line else None
