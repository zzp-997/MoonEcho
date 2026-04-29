"""AI 打招呼语生成相关请求/响应模型。

用于好友申请场景下 AI 辅助生成打招呼语的功能。

设计要点：
1. 三种风格：温暖型、轻松型、真诚型
2. 基于目标用户公开动态和双方共同点生成
3. 频率限制：每用户每天最多 10 次
4. 打招呼语长度：50-200 字
"""
from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 枚举类型
# ---------------------------------------------------------------------------

class GreetingType(str, Enum):
    """打招呼语类型枚举。"""

    WARM = "warm"       # 温暖型
    CASUAL = "casual"   # 轻松型
    SINCERE = "sincere"  # 真诚型


class GreetingContextType(str, Enum):
    """打招呼语场景类型枚举。"""

    FRIEND_REQUEST = "friend_request"  # 好友申请


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class GenerateGreetingRequest(BaseSchema):
    """生成打招呼语请求模型。"""

    target_user_id: str = Field(
        ...,
        description="目标用户ID（好友申请的接收者）",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    context_type: GreetingContextType = Field(
        default=GreetingContextType.FRIEND_REQUEST,
        description="场景类型，默认为好友申请",
        examples=["friend_request"],
    )

    @field_validator("target_user_id")
    @classmethod
    def validate_target_user_id(cls, v: str) -> str:
        """验证目标用户ID。"""
        v = v.strip()
        if not v:
            raise ValueError("目标用户ID不能为空")
        return v


# ---------------------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------------------

class GreetingItem(BaseSchema):
    """单条打招呼语。"""

    type: GreetingType = Field(..., description="打招呼语类型")
    content: str = Field(..., description="打招呼语内容")


class GreetingBasis(BaseSchema):
    """打招呼语生成依据。"""

    has_public_posts: bool = Field(
        default=False,
        description="目标用户是否有公开动态",
    )
    common_interests: list[str] = Field(
        default_factory=list,
        description="双方共同兴趣标签",
        examples=[["摄影", "晚霞"]],
    )
    same_age_group: bool = Field(
        default=False,
        description="是否处于相似年龄段",
    )
    same_city: bool = Field(
        default=False,
        description="是否同城",
    )


class GenerateGreetingResponse(BaseSchema):
    """生成打招呼语响应模型。"""

    greetings: list[GreetingItem] = Field(
        default_factory=list,
        description="生成的打招呼语列表（3个版本）",
    )
    based_on: GreetingBasis = Field(
        default_factory=GreetingBasis,
        description="生成依据信息",
    )
    remaining_count: int = Field(
        default=0,
        description="今日剩余生成次数",
    )
    is_fallback: bool = Field(
        default=False,
        description="是否为降级预设内容（AI服务不可用时返回）",
    )


# ---------------------------------------------------------------------------
# 频率限制响应
# ---------------------------------------------------------------------------

class GreetingQuotaResponse(BaseSchema):
    """打招呼语生成配额响应。"""

    daily_limit: int = Field(default=10, description="每日生成次数限制")
    used: int = Field(default=0, description="已使用次数")
    remaining: int = Field(default=10, description="剩余次数")
    can_generate: bool = Field(default=True, description="是否可以继续生成")
