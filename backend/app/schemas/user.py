from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    """用户公共字段。"""

    username: str = Field(..., min_length=1, max_length=50, description="登录账号")
    nickname: str | None = Field(None, max_length=100, description="显示昵称")
    email: str | None = Field(None, max_length=100, description="邮箱")
    phone: str | None = Field(None, max_length=20, description="手机号")
    remark: str | None = Field(None, max_length=500, description="备注")


class UserCreate(UserBase):
    """创建用户请求体（包含密码）。"""

    nickname: str = Field(..., min_length=1, max_length=100, description="显示昵称")
    password: str = Field(..., min_length=6, max_length=100, description="登录密码（至少 6 位）")
    role: UserRole = Field(default=UserRole.STAFF, description="角色：ADMIN/STAFF")

    @field_validator("username", "nickname", "password")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("该字段不能为空")
        return v


class UserUpdate(BaseModel):
    """更新用户请求体（所有字段可选）。"""

    nickname: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    avatar: str | None = Field(None, max_length=255)
    remark: str | None = Field(None, max_length=500)
    role: UserRole | None = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求体。"""

    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码（至少 8 位）")


class UserResponse(UserBase):
    """用户信息响应体（不含密码）。"""

    id: int
    avatar: str | None = None
    status: int
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
