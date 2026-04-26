"""通知相关请求/响应模型。

包含通知列表、通知设置等 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema, PaginatedResponse


# ---------------------------------------------------------------------------
# 通知类型枚举（与前端保持一致）
# ---------------------------------------------------------------------------

class NotificationType:
    """通知类型常量。

    分类：
    - 系统通知：system, update
    - AI 相关：ai_care, weekly_report
    - 危机干预：crisis_alert, crisis_follow
    - 社交相关：friend_request, friend_accept, treehole_reply, square_comment, square_like
    """
    # 系统通知
    SYSTEM = "system"
    UPDATE = "update"

    # AI 相关
    AI_CARE = "ai_care"
    WEEKLY_REPORT = "weekly_report"

    # 危机干预
    CRISIS_ALERT = "crisis_alert"
    CRISIS_FOLLOW = "crisis_follow"

    # 社交相关
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPT = "friend_accept"
    TREEHOLE_REPLY = "treehole_reply"
    SQUARE_COMMENT = "square_comment"
    SQUARE_LIKE = "square_like"


# ---------------------------------------------------------------------------
# 通知响应模型
# ---------------------------------------------------------------------------

class NotificationResponse(BaseSchema):
    """通知响应模型。"""

    id: str = Field(..., description="通知ID")
    type: str = Field(..., description="通知类型")
    title: str = Field(..., description="通知标题")
    content: str | None = Field(None, description="通知内容")
    payload: dict[str, Any] | None = Field(None, description="附加数据")
    is_read: bool = Field(..., description="是否已读")
    read_at: datetime | None = Field(None, description="已读时间")
    created_at: datetime = Field(..., description="创建时间")


class NotificationListResponse(PaginatedResponse[NotificationResponse]):
    """通知列表分页响应模型。"""

    unread_count: int = Field(default=0, ge=0, description="未读数量")


# ---------------------------------------------------------------------------
# 通知设置模型
# ---------------------------------------------------------------------------

# 默认开启的通知类型
DEFAULT_ENABLED_TYPES = [
    NotificationType.SYSTEM,
    NotificationType.UPDATE,
    NotificationType.AI_CARE,
    NotificationType.WEEKLY_REPORT,
    NotificationType.CRISIS_ALERT,
    NotificationType.CRISIS_FOLLOW,
    NotificationType.FRIEND_REQUEST,
    NotificationType.FRIEND_ACCEPT,
    NotificationType.TREEHOLE_REPLY,
    NotificationType.SQUARE_COMMENT,
    NotificationType.SQUARE_LIKE,
]

# 默认关闭的通知类型（营销类）
DEFAULT_DISABLED_TYPES = []


class NotificationSettingResponse(BaseSchema):
    """通知设置响应模型。"""

    push_enabled: bool = Field(..., description="是否开启推送")
    types_enabled: dict[str, bool] = Field(
        ...,
        description="各类型通知开关，键为类型名，值为是否开启",
    )


class NotificationSettingUpdateRequest(BaseSchema):
    """通知设置更新请求模型。"""

    push_enabled: bool | None = Field(
        None,
        description="是否开启推送，不传则不修改",
    )
    types_enabled: dict[str, bool] | None = Field(
        None,
        description="各类型通知开关，不传则不修改",
    )


# ---------------------------------------------------------------------------
# 推送频率控制配置
# ---------------------------------------------------------------------------

class PushFrequencyConfig:
    """推送频率控制配置。

    定义各类型推送的频率限制。
    """

    # 危机干预推送：每分钟最多 1 条（高优先级）
    CRISIS_LIMITS = {"max_count": 1, "window_seconds": 60}

    # AI 关怀推送：每小时最多 1 条
    AI_CARE_LIMITS = {"max_count": 1, "window_seconds": 3600}

    # 好友申请推送：每分钟最多 3 条
    FRIEND_REQUEST_LIMITS = {"max_count": 3, "window_seconds": 60}

    # 社交互动推送：每分钟最多 5 条
    SOCIAL_LIMITS = {"max_count": 5, "window_seconds": 60}

    # 系统推送：每小时最多 10 条
    SYSTEM_LIMITS = {"max_count": 10, "window_seconds": 3600}

    # 通知合并窗口（秒）
    MERGE_WINDOW_SECONDS = 300  # 5 分钟


# ---------------------------------------------------------------------------
# 推送请求模型
# ---------------------------------------------------------------------------

class PushRequest(BaseSchema):
    """推送请求模型（内部使用）。"""

    user_id: str = Field(..., description="目标用户ID")
    notification_type: str = Field(..., description="通知类型")
    title: str = Field(..., description="推送标题")
    content: str | None = Field(None, description="推送内容")
    payload: dict[str, Any] | None = Field(None, description="附加数据")
    device_token: str | None = Field(None, description="设备推送Token")


class PushResult(BaseSchema):
    """推送结果模型。"""

    success: bool = Field(..., description="是否成功")
    message_id: str | None = Field(None, description="推送消息ID")
    notification_id: str | None = Field(None, description="通知记录ID")
    merged: bool = Field(default=False, description="是否合并到已有通知")
    merged_count: int = Field(default=0, ge=0, description="合并的通知数量")
    error_message: str | None = Field(None, description="错误信息")
