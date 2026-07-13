from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SystemConfig(Base, TimestampMixin):
    """
    系统配置表（sys_config），键值对存储可运行时修改的配置。

    常用 key：
    - app_name：项目显示名称
    - app_subtitle：登录页副标题
    - logo_path：Logo 相对路径（如 branding/logo.png）
    """

    __tablename__ = "sys_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="配置键")
    value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="配置值")
