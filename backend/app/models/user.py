from sqlalchemy import Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    """
    系统用户表（sys_user）。

    status：1=正常，0=禁用
    role：ADMIN=管理员，STAFF=普通员工
    """

    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="登录账号")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="bcrypt 密码哈希")
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="显示昵称")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="手机号")
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="头像 URL")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="状态：1=正常，0=禁用")
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.STAFF.value, nullable=False, comment="角色：ADMIN/STAFF"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")
