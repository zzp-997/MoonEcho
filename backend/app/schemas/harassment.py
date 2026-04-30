"""骚扰检测相关的 Pydantic Schema 定义。

提供骚扰检测结果和安全提示的请求/响应模型。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 骚扰检测级别枚举
# ---------------------------------------------------------------------------

class HarassmentLevel(str, Enum):
    """骚扰检测级别。"""

    NONE = "none"           # 无异常
    WARN = "warn"           # 提醒（建议性，不强制）
    RATE_LIMIT = "rate_limit"  # 限速（强制执行）
    AUTO_DND = "auto_dnd"   # 自动勿扰模式
    SAFETY_ALERT = "safety_alert"  # 安全警告


# ---------------------------------------------------------------------------
# 对话安全提示响应
# ---------------------------------------------------------------------------

class SafetyTipResponse(BaseSchema):
    """对话安全提示响应模型。"""

    show_tip: bool = Field(..., description="是否显示安全提示")
    message: str | None = Field(None, description="提示消息")
    actions: list[str] = Field(default_factory=list, description="建议的操作列表")


# ---------------------------------------------------------------------------
# 社交能量状态响应（用于骚扰检测触发）
# ---------------------------------------------------------------------------

class SocialEnergyAlertResponse(BaseSchema):
    """社交能量警报响应模型。"""

    energy_level: str = Field(..., description="能量级别：normal/low/depleted")
    current_value: float = Field(..., description="当前能量值")
    threshold: float = Field(..., description="触发的阈值")
    message: str = Field(..., description="提示消息")
    suggested_actions: list[str] = Field(default_factory=list, description="建议的操作")
    auto_dnd_available: bool = Field(False, description="是否可以开启自动勿扰")


# ---------------------------------------------------------------------------
# 骚扰检测结果响应
# ---------------------------------------------------------------------------

class HarassmentCheckResponse(BaseSchema):
    """骚扰检测结果响应模型。"""

    has_warning: bool = Field(False, description="是否有警告")
    has_rate_limit: bool = Field(False, description="是否有限速")
    has_safety_alert: bool = Field(False, description="是否有安全警报")
    warning_messages: list[str] = Field(default_factory=list, description="警告消息列表")
    rate_limit_message: str | None = Field(None, description="限速消息")
    safety_actions: list[str] = Field(default_factory=list, description="建议的安全操作")


# ---------------------------------------------------------------------------
# 聊天证据保全请求/响应
# ---------------------------------------------------------------------------

class ChatEvidenceRequest(BaseSchema):
    """聊天证据保全请求模型。"""

    conversation_id: str = Field(..., description="会话ID")
    message_ids: list[str] = Field(default_factory=list, description="要保全的消息ID列表")


class ChatEvidenceItem(BaseSchema):
    """聊天证据项模型。"""

    evidence_id: str = Field(..., description="证据ID")
    conversation_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息ID")
    content_preview: str | None = Field(None, description="内容预览（脱敏）")
    recorded_at: datetime = Field(..., description="记录时间")
    expires_at: datetime | None = Field(None, description="过期时间")


class ChatEvidenceResponse(BaseSchema):
    """聊天证据保全响应模型。"""

    evidence_ids: list[str] = Field(default_factory=list, description="证据ID列表")
    message: str = Field(..., description="提示消息")
    expires_in_days: int = Field(30, description="证据保留天数")


# ---------------------------------------------------------------------------
# 一键屏蔽请求
# ---------------------------------------------------------------------------

class OneClickBlockRequest(BaseSchema):
    """一键屏蔽请求模型。"""

    user_id: str = Field(..., description="要屏蔽的用户ID")
    reason: str | None = Field(None, max_length=200, description="屏蔽原因（可选）")
    report_as_well: bool = Field(False, description="是否同时举报")


class OneClickBlockResponse(BaseSchema):
    """一键屏蔽响应模型。"""

    blocked: bool = Field(True, description="是否屏蔽成功")
    reported: bool = Field(False, description="是否同时举报")
    block_id: str = Field(..., description="屏蔽记录ID")
    report_id: str | None = Field(None, description="举报记录ID（如果同时举报）")
    message: str = Field(..., description="提示消息")


# ---------------------------------------------------------------------------
# 跨场景追踪警报
# ---------------------------------------------------------------------------

class CrossSceneAlert(BaseSchema):
    """跨场景追踪警报模型。"""

    target_user_id: str = Field(..., description="追踪目标用户ID")
    scenes: list[str] = Field(default_factory=list, description="出现的场景列表")
    scene_count: int = Field(0, description="场景数量")
    first_seen: datetime | None = Field(None, description="首次出现时间")
    message: str | None = Field(None, description="提示消息")


# ---------------------------------------------------------------------------
# 对话模式分析结果
# ---------------------------------------------------------------------------

class ConversationPatternResult(BaseSchema):
    """对话模式分析结果模型。"""

    is_abnormal: bool = Field(False, description="是否异常")
    pattern_type: str | None = Field(None, description="异常类型：consecutive/imbalance/no_response")
    consecutive_count: int = Field(0, description="连续消息数")
    imbalance_ratio: float | None = Field(None, description="消息不平衡比例")
    message: str | None = Field(None, description="提示消息")


# ---------------------------------------------------------------------------
# 勿扰模式设置
# ---------------------------------------------------------------------------

class DoNotDisturbSettings(BaseSchema):
    """勿扰模式设置模型。"""

    enabled: bool = Field(False, description="是否开启勿扰模式")
    auto_trigger: bool = Field(True, description="是否允许自动触发（能量耗尽时）")
    energy_threshold: int = Field(20, ge=0, le=50, description="自动触发的能量阈值")
    quiet_hours_start: str | None = Field(None, description="静默时段开始（如 '22:00'）")
    quiet_hours_end: str | None = Field(None, description="静默时段结束（如 '07:00'）")


class DoNotDisturbStatus(BaseSchema):
    """勿扰模式状态模型。"""

    enabled: bool = Field(False, description="是否开启")
    auto_triggered: bool = Field(False, description="是否为自动触发")
    remaining_minutes: int = Field(0, description="剩余时间（分钟）")
    can_manually_disable: bool = Field(True, description="是否可以手动关闭")


class UpdateDoNotDisturbRequest(BaseSchema):
    """更新勿扰模式请求模型。"""

    enabled: bool = Field(..., description="是否开启")
    duration_hours: int | None = Field(None, ge=1, le=24, description="持续时长（小时）")


# ---------------------------------------------------------------------------
# 用户边界设置
# ---------------------------------------------------------------------------

class UserBoundarySettings(BaseSchema):
    """用户边界设置模型。"""

    allow_stranger_messages: bool = Field(True, description="是否允许陌生人发消息")
    require_friend_for_chat: bool = Field(False, description="是否需要是好友才能聊天")
    auto_block_on_report: bool = Field(True, description="举报后自动屏蔽")
    show_online_status: bool = Field(False, description="是否显示在线状态")
    show_read_status: bool = Field(True, description="是否显示已读状态")


class UpdateBoundarySettingsRequest(BaseSchema):
    """更新边界设置请求模型。"""

    allow_stranger_messages: bool | None = Field(None, description="是否允许陌生人发消息")
    require_friend_for_chat: bool | None = Field(None, description="是否需要是好友才能聊天")
    auto_block_on_report: bool | None = Field(None, description="举报后自动屏蔽")
    show_online_status: bool | None = Field(None, description="是否显示在线状态")
    show_read_status: bool | None = Field(None, description="是否显示已读状态")
