from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """用户名密码登录请求体。"""

    username: str = Field(..., min_length=1, max_length=50, description="登录账号")
    password: str = Field(..., min_length=1, max_length=100, description="登录密码")


class TokenResponse(BaseModel):
    """登录成功后返回的 Token 信息。"""

    access_token: str = Field(..., description="JWT Access Token")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_in: int = Field(..., description="过期时长（秒）")
