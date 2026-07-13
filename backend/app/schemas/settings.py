from pydantic import BaseModel, Field


class BrandingResponse(BaseModel):
    """公开品牌配置（登录页 / 侧栏等）。"""

    app_name: str = Field(description="项目显示名称")
    app_subtitle: str = Field(description="登录页副标题")
    logo_url: str | None = Field(default=None, description="Logo 访问 URL，未上传时为 null")


class BrandingUpdate(BaseModel):
    """管理员更新品牌文案。"""

    app_name: str = Field(min_length=1, max_length=100, description="项目显示名称")
    app_subtitle: str = Field(min_length=1, max_length=200, description="登录页副标题")
