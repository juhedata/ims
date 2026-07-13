from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    """客户。"""

    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="客户ID")
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, comment="客户名称")
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="权重，越高越靠前")
