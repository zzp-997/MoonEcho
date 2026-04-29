"""好友相关请求/响应模型。

包含好友申请、好友列表、拉黑相关的 Schema 定义。

设计要点：
1. 好友申请：支持打招呼语，可由 AI 协助生成
2. 好友列表：显示好友基本信息和会话状态
3. 拉黑：支持拉黑原因记录
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 状态枚举
# ---------------------------------------------------------------------------

class FriendRequestStatus(str, Enum):
    """好友申请状态枚举。"""

    PENDING = "pending"     # 待处理
    ACCEPTED = "accepted"   # 已同意
    REJECTED = "rejected"   # 已忽略
    EXPIRED = "expired"     # 已过期


# ---------------------------------------------------------------------------
# 好友申请请求
# ---------------------------------------------------------------------------

class SendFriendRequestRequest(BaseSchema):
    """发送好友申请请求模型。"""

    recipient_id: str = Field(..., description="接收者用户ID")
    greeting_message: str | None = Field(
        None,
        max_length=200,
        description="打招呼语（最多200字）",
    )


class AcceptFriendRequestRequest(BaseSchema):
    """同意好友申请请求模型（可选：回复打招呼）。"""

    reply_message: str | None = Field(
        None,
        max_length=100,
        description="回复打招呼（可选）",
    )


# ---------------------------------------------------------------------------
# 好友申请响应
# ---------------------------------------------------------------------------

class FriendRequestSender(BaseSchema):
    """好友申请发送者信息。"""

    user_id: str = Field(..., description="用户ID")
    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")


class FriendRequestResponse(BaseSchema):
    """好友申请响应模型。"""

    id: str = Field(..., description="申请ID")
    sender: FriendRequestSender = Field(..., description="发送者信息")
    greeting_message: str | None = Field(None, description="打招呼语")
    status: FriendRequestStatus = Field(..., description="申请状态")
    created_at: datetime = Field(..., description="申请时间")
    expires_at: datetime = Field(..., description="过期时间")
    is_expired: bool = Field(False, description="是否已过期")


class FriendRequestListResponse(BaseSchema):
    """好友申请列表响应模型。"""

    data: list[FriendRequestResponse] = Field(default_factory=list, description="申请列表")
    pending_count: int = Field(0, description="待处理数量")
    pagination: dict = Field(default_factory=dict, description="分页信息")


class SendFriendRequestResponse(BaseSchema):
    """发送好友申请响应模型。"""

    request_id: str = Field(..., description="申请ID")
    status: FriendRequestStatus = Field(FriendRequestStatus.PENDING, description="申请状态")
    expires_at: datetime = Field(..., description="过期时间")
    greeting_message: str | None = Field(None, description="打招呼语")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 好友列表响应
# ---------------------------------------------------------------------------

class FriendUserInfo(BaseSchema):
    """好友用户信息。"""

    user_id: str = Field(..., description="用户ID")
    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    is_official_ai: bool = Field(False, description="是否官方AI账号")


class FriendResponse(BaseSchema):
    """好友响应模型。"""

    friendship_id: str = Field(..., description="好友关系ID")
    friend: FriendUserInfo = Field(..., description="好友信息")
    conversation_id: str | None = Field(None, description="会话ID")
    last_message_preview: str | None = Field(None, description="最后消息预览")
    last_message_at: datetime | None = Field(None, description="最后消息时间")
    created_at: datetime = Field(..., description="成为好友时间")


class FriendListResponse(BaseSchema):
    """好友列表响应模型。"""

    data: list[FriendResponse] = Field(default_factory=list, description="好友列表")
    total_count: int = Field(0, description="好友总数")
    pagination: dict = Field(default_factory=dict, description="分页信息")


# ---------------------------------------------------------------------------
# 拉黑相关
# ---------------------------------------------------------------------------

class BlockUserRequest(BaseSchema):
    """拉黑用户请求模型。"""

    reason: str | None = Field(
        None,
        max_length=200,
        description="拉黑原因（可选）",
    )


class BlockedUserResponse(BaseSchema):
    """被拉黑用户响应模型。"""

    block_id: str = Field(..., description="拉黑记录ID")
    blocked_user: FriendUserInfo = Field(..., description="被拉黑用户信息")
    reason: str | None = Field(None, description="拉黑原因")
    created_at: datetime = Field(..., description="拉黑时间")


class BlockListResponse(BaseSchema):
    """拉黑列表响应模型。"""

    data: list[BlockedUserResponse] = Field(default_factory=list, description="拉黑列表")
    total_count: int = Field(0, description="拉黑总数")
    pagination: dict = Field(default_factory=dict, description="分页信息")


class BlockUserResponse(BaseSchema):
    """拉黑用户响应模型。"""

    block_id: str = Field(..., description="拉黑记录ID")
    blocked_user: FriendUserInfo = Field(..., description="被拉黑用户信息")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 删除好友响应
# ---------------------------------------------------------------------------

class DeleteFriendResponse(BaseSchema):
    """删除好友响应模型。"""

    deleted: bool = Field(True, description="是否删除成功")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 同意/忽略好友申请响应
# ---------------------------------------------------------------------------

class HandleFriendRequestResponse(BaseSchema):
    """处理好友申请响应模型。"""

    success: bool = Field(True, description="是否处理成功")
    message: str = Field(..., description="提示消息")
    conversation_id: str | None = Field(None, description="会话ID（同意时返回）")


# ---------------------------------------------------------------------------
# 官方 AI 账号信息
# ---------------------------------------------------------------------------

class OfficialAIInfo(BaseSchema):
    """官方 AI 账号信息。"""

    user_id: str = Field(..., description="用户ID")
    nickname: str = Field(..., description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    persona_type: str = Field(..., description="人设类型：xiaowen/lahei/ali")


# ---------------------------------------------------------------------------
# 冷却期检查响应
# ---------------------------------------------------------------------------

class CooldownCheckResponse(BaseSchema):
    """冷却期检查响应模型。"""

    can_send: bool = Field(..., description="是否可以发送申请")
    cooldown_until: datetime | None = Field(None, description="冷却期结束时间")
    request_count_in_30_days: int = Field(0, description="30天内已发送申请次数")
    max_requests_per_30_days: int = Field(3, description="30天最大申请次数")
    message: str = Field(..., description="提示消息")