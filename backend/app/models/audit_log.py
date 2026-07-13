from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """系统审计日志：记录谁在什么时间对什么资源做了什么操作。"""

    __tablename__ = "sys_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, index=True, comment="操作人 ID"
    )
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="操作人账号/昵称快照")
    action: Mapped[str] = mapped_column(String(30), nullable=False, index=True, comment="操作类型")
    module: Mapped[str] = mapped_column(String(30), nullable=False, index=True, comment="业务模块")
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="资源类型")
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="资源标识")
    resource_name: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="资源名称/单号")
    summary: Mapped[str] = mapped_column(String(500), nullable=False, comment="操作摘要")
    before_data: Mapped[str | None] = mapped_column(Text, nullable=True, comment="变更前数据 JSON")
    after_data: Mapped[str | None] = mapped_column(Text, nullable=True, comment="变更后数据 JSON")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, comment="客户端 IP")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, comment="操作时间")
