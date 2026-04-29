"""私聊相关的 Pydantic Schema 定义。

提供私聊功能的请求/响应模型：
- WebSocket 消息类型
- 会话列表响应
- 历史消息响应
- 发送消息请求/响应
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 消息类型枚举
# ---------------------------------------------------------------------------

class MessageType(str, Enum):
    """消息类型枚举。"""

    TEXT = "text"      # 文字消息
    IMAGE = "image"    # 图片消息


class WsEventType(str, Enum):
    """WebSocket 事件类型枚举。"""

    # 客户端 -> 服务端
    PING = "ping"                    # 心跳请求
    SEND_MESSAGE = "send_message"    # 发送消息
    MARK_READ = "mark_read"          # 标记已读
    PULL_OFFLINE = "pull_offline"    # 拉取离线消息

    # 服务端 -> 客户端
    PONG = "pong"                    # 心跳响应
    NEW_MESSAGE = "new_message"      # 新消息通知
    MESSAGE_SENT = "message_sent"    # 消息发送成功确认
    MESSAGE_READ = "message_read"    # 消息已读回执
    ERROR = "error"                  # 错误消息


# ---------------------------------------------------------------------------
# WebSocket 消息模型
# ---------------------------------------------------------------------------

class WsMessage(BaseSchema):
    """WebSocket 消息基础模型。"""

    type: WsEventType = Field(..., description="消息类型")
    data: dict[str, Any] | None = Field(default=None, description="消息数据")


class WsPingMessage(BaseSchema):
    """WebSocket 心跳请求。"""

    type: WsEventType = Field(default=WsEventType.PING, description="消息类型")
    timestamp: datetime | None = Field(default=None, description="客户端时间戳")


class WsPongMessage(BaseSchema):
    """WebSocket 心跳响应。"""

    type: WsEventType = Field(default=WsEventType.PONG, description="消息类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="服务端时间戳")


class WsErrorMessage(BaseSchema):
    """WebSocket 错误消息。"""

    type: WsEventType = Field(default=WsEventType.ERROR, description="消息类型")
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")


# ---------------------------------------------------------------------------
# 消息相关模型
# ---------------------------------------------------------------------------

class SendMessageRequest(BaseSchema):
    """发送消息请求（WebSocket 和 HTTP 通用）。"""

    conversation_id: str = Field(..., description="会话ID")
    message_type: MessageType = Field(default=MessageType.TEXT, description="消息类型")
    content: str | None = Field(default=None, max_length=5000, description="消息内容（文字消息必填）")
    media_url: str | None = Field(default=None, description="媒体文件URL（图片消息必填）")
    client_message_id: str | None = Field(default=None, description="客户端消息ID（用于去重）")


class MessageSender(BaseSchema):
    """消息发送者信息。"""

    user_id: str = Field(..., description="用户ID")
    nickname: str | None = Field(default=None, description="昵称")
    avatar_url: str | None = Field(default=None, description="头像URL")


class MessageResponse(BaseSchema):
    """消息响应模型。"""

    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    sender: MessageSender = Field(..., description="发送者信息")
    message_type: MessageType = Field(..., description="消息类型")
    content: str | None = Field(default=None, description="消息内容")
    media_url: str | None = Field(default=None, description="媒体文件URL")
    is_read: bool = Field(default=False, description="是否已读")
    read_at: datetime | None = Field(default=None, description="已读时间")
    created_at: datetime = Field(..., description="创建时间")
    is_expired: bool = Field(default=False, description="图片是否已过期")


class MessageSentResponse(BaseSchema):
    """消息发送成功响应（WebSocket 确认）。"""

    message: MessageResponse = Field(..., description="消息详情")
    client_message_id: str | None = Field(default=None, description="客户端消息ID")


class MarkReadRequest(BaseSchema):
    """标记已读请求。"""

    conversation_id: str = Field(..., description="会话ID")
    last_message_id: str = Field(..., description="最后一条已读消息ID")


class PullOfflineRequest(BaseSchema):
    """拉取离线消息请求。"""

    after_message_id: str | None = Field(default=None, description="从此消息ID之后拉取")


class PullOfflineResponse(BaseSchema):
    """拉取离线消息响应。"""

    messages: list[MessageResponse] = Field(default_factory=list, description="消息列表")
    has_more: bool = Field(default=False, description="是否还有更多消息")


# ---------------------------------------------------------------------------
# 会话相关模型
# ---------------------------------------------------------------------------

class ConversationUser(BaseSchema):
    """会话中的用户信息。"""

    user_id: str = Field(..., description="用户ID")
    nickname: str | None = Field(default=None, description="昵称")
    avatar_url: str | None = Field(default=None, description="头像URL")
    is_official_ai: bool = Field(default=False, description="是否为官方AI账号")


class ConversationResponse(BaseSchema):
    """会话响应模型。"""

    id: str = Field(..., description="会话ID")
    friend: ConversationUser = Field(..., description="好友信息")
    last_message: MessageResponse | None = Field(default=None, description="最后一条消息")
    last_message_at: datetime | None = Field(default=None, description="最后消息时间")
    unread_count: int = Field(default=0, description="未读消息数")
    created_at: datetime = Field(..., description="创建时间")


class ConversationListResponse(BaseSchema):
    """会话列表响应。"""

    data: list[ConversationResponse] = Field(default_factory=list, description="会话列表")
    total_count: int = Field(default=0, description="总数")
    pagination: dict[str, Any] = Field(default_factory=dict, description="分页信息")


class ConversationDetailResponse(BaseSchema):
    """会话详情响应。"""

    id: str = Field(..., description="会话ID")
    friend: ConversationUser = Field(..., description="好友信息")
    friendship_id: str | None = Field(default=None, description="好友关系ID")
    created_at: datetime = Field(..., description="创建时间")


class MessageListResponse(BaseSchema):
    """消息列表响应。"""

    data: list[MessageResponse] = Field(default_factory=list, description="消息列表")
    conversation_id: str = Field(..., description="会话ID")
    pagination: dict[str, Any] = Field(default_factory=dict, description="分页信息")


# ---------------------------------------------------------------------------
# 图片上传响应
# ---------------------------------------------------------------------------

class ImageUploadResponse(BaseSchema):
    """图片上传响应。"""

    url: str = Field(..., description="图片URL")
    expires_at: datetime | None = Field(default=None, description="过期时间（90天后）")
    message: str = Field(default="图片上传成功", description="提示信息")
