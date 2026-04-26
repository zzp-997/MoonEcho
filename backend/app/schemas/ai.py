"""AI 对话相关请求/响应模型。

包含对话请求、对话响应、会话列表、开场白等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 对话请求
# ---------------------------------------------------------------------------

class ChatRequest(BaseSchema):
    """对话请求体。"""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户消息内容",
        examples=["我今天感觉很累，工作压力好大"],
    )
    personality: str = Field(
        default="xiaowen",
        description="AI性格：xiaowen(小温-温柔倾听者)/laohei(老黑-毒舌吐槽者)/ali(阿理-理性开导者)",
        examples=["xiaowen"],
    )
    conversation_id: str | None = Field(
        default=None,
        description="对话ID（可选，续聊时传入，首次对话不需要）",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """验证消息内容。"""
        v = v.strip()
        if not v:
            raise ValueError("消息内容不能为空")
        if len(v) > 2000:
            raise ValueError("消息内容不能超过 2000 个字符")
        return v

    @field_validator("personality")
    @classmethod
    def validate_personality(cls, v: str) -> str:
        """验证性格标识。"""
        valid_personalities = ("xiaowen", "laohei", "ali")
        if v not in valid_personalities:
            raise ValueError(f"无效的性格标识: {v}，可用选项: {', '.join(valid_personalities)}")
        return v


# ---------------------------------------------------------------------------
# 对话响应
# ---------------------------------------------------------------------------

class ChatResponse(BaseSchema):
    """对话响应体。"""

    conversation_id: str = Field(..., description="对话ID")
    message: str = Field(..., description="AI回复内容")
    personality: str = Field(..., description="当前AI性格")
    crisis_level: str | None = Field(
        default=None,
        description="危机级别（如果检测到危机关键词）：low/medium/high",
    )
    crisis_keywords: str | None = Field(
        default=None,
        description="匹配到的危机关键词（逗号分隔）",
    )


# ---------------------------------------------------------------------------
# 会话列表
# ---------------------------------------------------------------------------

class ConversationListItem(BaseSchema):
    """会话列表项。"""

    id: str = Field(..., description="会话ID")
    personality: str = Field(..., description="AI性格")
    title: str | None = Field(default=None, description="会话标题")
    last_message: str | None = Field(
        default=None,
        description="最后一条消息预览（最多100字）",
    )
    last_message_at: datetime | None = Field(
        default=None,
        description="最后消息时间",
    )
    created_at: datetime = Field(..., description="创建时间")


class ConversationListResponse(BaseSchema):
    """会话列表响应。"""

    items: list[ConversationListItem] = Field(
        default_factory=list,
        description="会话列表",
    )
    total: int = Field(default=0, description="总数")


# ---------------------------------------------------------------------------
# 开场白
# ---------------------------------------------------------------------------

class GreetingRequest(BaseSchema):
    """开场白请求体。"""

    personality: str | None = Field(
        default=None,
        description="AI性格（可选，默认使用上次选择的性格或默认性格）",
        examples=["xiaowen"],
    )

    @field_validator("personality")
    @classmethod
    def validate_personality(cls, v: str | None) -> str | None:
        """验证性格标识。"""
        if v is None:
            return v
        valid_personalities = ("xiaowen", "laohei", "ali")
        if v not in valid_personalities:
            raise ValueError(f"无效的性格标识: {v}，可用选项: {', '.join(valid_personalities)}")
        return v


class GreetingResponse(BaseSchema):
    """开场白响应体。"""

    greeting: str = Field(..., description="AI开场白内容")
    personality: str = Field(..., description="当前AI性格")
    conversation_id: str = Field(..., description="对话ID（用于后续对话）")


# ---------------------------------------------------------------------------
# 配额检查
# ---------------------------------------------------------------------------

class QuotaResponse(BaseSchema):
    """配额检查响应体。"""

    daily_limit: int = Field(..., description="每日对话限制")
    used: int = Field(default=0, description="已使用次数")
    remaining: int = Field(default=0, description="剩余次数")
    can_chat: bool = Field(..., description="是否可以继续对话")


# ---------------------------------------------------------------------------
# AI 性格信息
# ---------------------------------------------------------------------------

class PersonaInfo(BaseSchema):
    """AI 性格信息。"""

    id: str = Field(..., description="性格标识")
    name: str = Field(..., description="显示名称")
    description: str = Field(..., description="性格描述")
    greeting_preview: str = Field(..., description="开场白预览")
    traits: list[str] = Field(default_factory=list, description="性格特点标签")


class PersonaListResponse(BaseSchema):
    """AI 性格列表响应。"""

    items: list[PersonaInfo] = Field(
        default_factory=list,
        description="性格列表",
    )
