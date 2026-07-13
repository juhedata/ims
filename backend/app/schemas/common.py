from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class R(BaseModel, Generic[T]):
    """
    统一 API 响应包装器。

    code：业务状态码（0=成功，非 0=失败）
    msg：提示信息
    data：业务数据，泛型，可为任意类型或 None
    """

    code: int = 0
    msg: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: T = None, msg: str = "success") -> "R[T]":
        """返回成功响应。"""
        return cls(code=0, msg=msg, data=data)

    @classmethod
    def fail(cls, msg: str = "操作失败", code: int = -1) -> "R[None]":
        """返回失败响应（业务错误，HTTP 状态码仍为 200）。"""
        return cls(code=code, msg=msg, data=None)


class PageResult(BaseModel, Generic[T]):
    """分页查询结果。"""

    total: int
    page: int
    page_size: int
    items: list[T]
