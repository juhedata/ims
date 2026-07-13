from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SequenceCounter(Base, TimestampMixin):
    """按日递增的单号序列计数器（JIN / JOUT）。"""

    __tablename__ = "sys_sequence"
    __table_args__ = (UniqueConstraint("seq_type", "seq_date", name="uk_seq_type_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seq_type: Mapped[str] = mapped_column(String(10), nullable=False, comment="序列类型：JIN / JOUT")
    seq_date: Mapped[str] = mapped_column(String(8), nullable=False, comment="日期 YYYYMMDD")
    current_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="当前序号")
