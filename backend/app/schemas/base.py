"""Pydantic 模型基类定义。

提供通用的请求/响应模型基类，减少各模块重复定义。
- BaseSchema: 所有 Schema 的基类，启用 from_attributes 支持 ORM 模型转换
- PaginationParams: 分页请求参数
- PaginatedResponse: 分页响应泛型模型
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Pydantic 模型基类。

    启用 from_attributes=True 以支持从 SQLAlchemy ORM 模型直接转换，
    所有业务 Schema 应继承此基类。
    """

    model_config = {"from_attributes": True}


class PaginationParams(BaseSchema):
    """分页请求参数模型。

    Attributes:
        page: 当前页码，从 1 开始
        page_size: 每页条数，默认 20，最大 100
    """

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")

    @property
    def offset(self) -> int:
        """计算 SQL 偏移量。"""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应泛型模型。

    用于统一分页接口的返回格式，data 字段支持任意类型的列表。

    Attributes:
        data: 当前页数据列表
        page: 当前页码
        page_size: 每页条数
        total: 总记录数
        has_more: 是否还有下一页
    """

    data: list[T] = Field(default_factory=list, description="当前页数据列表")
    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, description="每页条数")
    total: int = Field(ge=0, description="总记录数")
    has_more: bool = Field(description="是否还有下一页")

    @classmethod
    def create(
        cls,
        data: list[T],
        page: int,
        page_size: int,
        total: int,
    ) -> PaginatedResponse[T]:
        """便捷构造方法，自动计算 has_more。"""
        return cls(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
            has_more=page * page_size < total,
        )
