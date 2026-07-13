from sqlalchemy import ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PartnerGroup(Base, TimestampMixin):
    """往来单位分组。"""

    __tablename__ = "partner_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分组ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="分组名称")

    partners: Mapped[list["Partner"]] = relationship(back_populates="group")


class Partner(Base, TimestampMixin):
    """往来单位。"""

    __tablename__ = "partner"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="单位ID")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="单位名称")
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partner_group.id"), nullable=False, index=True, comment="分组ID"
    )
    partner_type: Mapped[int] = mapped_column(
        SmallInteger, default=0, nullable=False, comment="0=供应商&客户 1=客户 2=供应商"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="1=启用 0=停用")

    group: Mapped["PartnerGroup"] = relationship(back_populates="partners")

    @property
    def partner_group_id(self) -> int:
        return self.group_id

    @property
    def partner_group_name(self) -> str | None:
        return self.group.name if self.group else None
