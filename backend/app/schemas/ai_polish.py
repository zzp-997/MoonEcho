"""AI 文案润色相关请求/响应模型。

提供动态广场发布前 AI 润色功能的 Schema 定义：
- PolishRequest: 润色请求体
- PolishVersion: 润色版本
- PolishResponse: 润色响应体
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 润色风格枚举
# ---------------------------------------------------------------------------

class PolishStyle(str, Enum):
    """AI 润色风格枚举。"""

    WARM = "warm"      # 温暖治愈风：温柔、安慰、陪伴感
    FUNNY = "funny"    # 轻松幽默风：活泼、有趣、接地气
    SINCERE = "sincere"  # 真诚分享风：朴实、真挚、无修饰


# ---------------------------------------------------------------------------
# 润色请求
# ---------------------------------------------------------------------------

class PolishRequest(BaseSchema):
    """AI 文案润色请求体。"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="需要润色的原文内容，最多500字",
        examples=["今天心情不太好，工作压力好大"],
    )
    style: PolishStyle = Field(
        default=PolishStyle.WARM,
        description="润色风格：warm(温暖治愈风)/funny(轻松幽默风)/sincere(真诚分享风)",
        examples=["warm"],
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """验证内容。"""
        v = v.strip()
        if not v:
            raise ValueError("内容不能为空")
        if len(v) > 500:
            raise ValueError("内容不能超过 500 个字符")
        return v


# ---------------------------------------------------------------------------
# 润色响应
# ---------------------------------------------------------------------------

class PolishVersion(BaseSchema):
    """润色版本。"""

    id: int = Field(..., description="版本编号，从1开始")
    content: str = Field(..., description="润色后的内容")
    style: str = Field(..., description="润色风格")


class PolishResponse(BaseSchema):
    """AI 文案润色响应体。"""

    original: str = Field(..., description="原始内容")
    versions: list[PolishVersion] = Field(
        default_factory=list,
        description="润色版本列表，提供2个版本供用户选择",
    )
