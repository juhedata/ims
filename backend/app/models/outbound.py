from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import OperationStatus
from app.models.partner import Partner


class OutboundOrder(Base, TimestampMixin):
    """出库单。"""

    __tablename__ = "outbound_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True, comment="JOUT-单号")
    outbound_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="出库类型")
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("partner.id"), nullable=False, comment="往来单位")
    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="客户名称")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    operation_status: Mapped[str] = mapped_column(
        String(30), default=OperationStatus.INITIATED.value, nullable=False, index=True
    )
    total_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submitted_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["OutboundOrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
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


class OutboundOrderItem(Base):
    """出库单单品明细。"""

    __tablename__ = "outbound_order_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    outbound_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("outbound_order.id"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inventory_item.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_sku.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    order: Mapped["OutboundOrder"] = relationship(back_populates="items")
