from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CustomerResponse(BaseModel):
    id: int
    name: str
    weight: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=200)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("客户名称不能为空")
        return v
