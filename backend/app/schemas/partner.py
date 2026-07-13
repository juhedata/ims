from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class GroupCreate(BaseModel):
    name: str = Field(..., max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("分组名称不能为空")
        return v


class GroupUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("分组名称不能为空")
        return v


class GroupResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PartnerCreate(BaseModel):
    name: str = Field(..., max_length=200)
    group_id: int
    partner_type: int = 0
    remark: str | None = None
    status: int = 1

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("单位名称不能为空")
        return v


class PartnerUpdate(BaseModel):
    name: str | None = None
    group_id: int | None = None
    partner_type: int | None = None
    remark: str | None = None
    status: int | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("单位名称不能为空")
        return v


class PartnerResponse(BaseModel):
    id: int
    name: str
    group_id: int
    partner_group_id: int
    partner_group_name: str | None
    partner_type: int
    remark: str | None
    status: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
