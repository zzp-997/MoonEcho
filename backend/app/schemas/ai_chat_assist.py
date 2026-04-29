"""AI 聊天辅助相关的 Pydantic Schema 定义。

提供冷场救急、回复建议、语气优化、温柔退出的请求/响应模型。
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 话题建议（冷场救急）
# ---------------------------------------------------------------------------

class TopicSuggestionRequest(BaseSchema):
    """话题建议请求模型。"""

    conversation_id: str = Field(..., description="会话ID")
    context: str = Field(..., max_length=1000, description="对话上下文（最近几轮对话摘要）")


class TopicItem(BaseSchema):
    """单个话题建议。"""

    id: int = Field(..., description="话题序号")
    content: str = Field(..., description="话题内容")


class TopicSuggestionResponse(BaseSchema):
    """话题建议响应模型。"""

    type: str = Field("topic_suggestion", description="响应类型")
    topics: list[TopicItem] = Field(default_factory=list, description="话题建议列表")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 回复建议
# ---------------------------------------------------------------------------

class ReplySuggestionRequest(BaseSchema):
    """回复建议请求模型。"""

    conversation_id: str = Field(..., description="会话ID")
    context: str = Field(..., max_length=1000, description="对话上下文")
    last_message: str = Field(..., max_length=500, description="对方最后说的话")


class ReplyItem(BaseSchema):
    """单个回复建议。"""

    id: int = Field(..., description="回复序号")
    content: str = Field(..., description="回复内容")
    tone: str = Field(..., description="语气类型：温和/轻松/关心")


class ReplySuggestionResponse(BaseSchema):
    """回复建议响应模型。"""

    type: str = Field("reply_suggestion", description="响应类型")
    replies: list[ReplyItem] = Field(default_factory=list, description="回复建议列表")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 语气优化（润色）
# ---------------------------------------------------------------------------

class PolishRequest(BaseSchema):
    """语气优化请求模型。"""

    conversation_id: str | None = Field(None, description="会话ID（可选）")
    original_text: str = Field(..., min_length=1, max_length=500, description="用户原始输入")


class PolishResponse(BaseSchema):
    """语气优化响应模型。"""

    type: str = Field("polish", description="响应类型")
    original: str = Field(..., description="原始内容")
    polished: str = Field(..., description="润色后内容")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 温柔退出
# ---------------------------------------------------------------------------

class ExitSuggestionRequest(BaseSchema):
    """温柔退出请求模型。"""

    conversation_id: str = Field(..., description="会话ID")
    context: str = Field(..., max_length=1000, description="对话上下文")


class ExitItem(BaseSchema):
    """单个结束语建议。"""

    id: int = Field(..., description="结束语序号")
    content: str = Field(..., description="结束语内容")


class ExitSuggestionResponse(BaseSchema):
    """温柔退出响应模型。"""

    type: str = Field("exit_suggestion", description="响应类型")
    exits: list[ExitItem] = Field(default_factory=list, description="结束语建议列表")
    message: str = Field(..., description="提示消息")