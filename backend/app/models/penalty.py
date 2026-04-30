"""处罚记录模型。

实现 modules_design.md 7.4 规定的处罚梯度机制：

| 违规程度 | 首次 | 二次 | 三次 |
|---------|------|------|------|
| 轻微（消息过频） | 速率限制+警告 | 禁用24小时 | 禁用7天 |
| 中等（诱导引流） | 禁用24小时+警告 | 禁用7天 | 永久封禁 |
| 严重（性骚扰/PUA） | 永久封禁 | 永久封禁+设备标记 | 同左 |
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# 处罚类型枚举
# ---------------------------------------------------------------------------

class PenaltyType(str, Enum):
    """处罚类型。"""

    # 轻微违规
    RATE_LIMIT_WARN = "rate_limit_warn"      # 速率限制+警告
    DISABLE_24H = "disable_24h"              # 禁用24小时
    DISABLE_7D = "disable_7d"                # 禁用7天

    # 中等违规
    BAN_24H = "ban_24h"                      # 封禁24小时
    BAN_7D = "ban_7d"                        # 封禁7天
    BAN_PERMANENT = "ban_permanent"          # 永久封禁

    # 严重违规
    BAN_PERMANENT_DEVICE = "ban_permanent_device"  # 永久封禁+设备标记


class ViolationSeverity(str, Enum):
    """违规程度。"""

    MINOR = "minor"        # 轻微：消息过频
    MODERATE = "moderate"  # 中等：诱导引流
    SEVERE = "severe"      # 严重：性骚扰/PUA


class ViolationType(str, Enum):
    """违规类型。"""

    # 轻微违规
    MESSAGE_RATE_EXCEEDED = "message_rate_exceeded"    # 消息发送过快
    FRIEND_REQUEST_EXCEEDED = "friend_request_exceeded"  # 好友申请过多
    COMMENT_RATE_EXCEEDED = "comment_rate_exceeded"    # 评论过频

    # 中等违规
    PROMOTION_DETECTED = "promotion_detected"          # 广告引流
    CONTACT_INFO_INDUCED = "contact_info_induced"      # 诱导获取联系方式
    FAKE_CONTENT = "fake_content"                      # 虚假内容

    # 严重违规
    SEXUAL_HARASSMENT = "sexual_harassment"            # 性骚扰
    PUA_BEHAVIOR = "pua_behavior"                      # PUA行为
    FRAUD_ATTEMPT = "fraud_attempt"                    # 诈骗企图
    VIOLENCE_THREAT = "violence_threat"                # 暴力威胁


# ---------------------------------------------------------------------------
# 处罚梯度配置
# ---------------------------------------------------------------------------

# 处罚梯度表：{违规程度: {违规次数: 处罚类型}}
PENALTY_GRADIENT: dict[ViolationSeverity, dict[int, PenaltyType]] = {
    ViolationSeverity.MINOR: {
        1: PenaltyType.RATE_LIMIT_WARN,
        2: PenaltyType.DISABLE_24H,
        3: PenaltyType.DISABLE_7D,
    },
    ViolationSeverity.MODERATE: {
        1: PenaltyType.BAN_24H,
        2: PenaltyType.BAN_7D,
        3: PenaltyType.BAN_PERMANENT,
    },
    ViolationSeverity.SEVERE: {
        1: PenaltyType.BAN_PERMANENT,
        2: PenaltyType.BAN_PERMANENT_DEVICE,
        3: PenaltyType.BAN_PERMANENT_DEVICE,
    },
}

# 处罚持续时间配置（小时）
PENALTY_DURATION_HOURS: dict[PenaltyType, int | None] = {
    PenaltyType.RATE_LIMIT_WARN: None,       # 无固定时长，由规则引擎控制
    PenaltyType.DISABLE_24H: 24,
    PenaltyType.DISABLE_7D: 7 * 24,
    PenaltyType.BAN_24H: 24,
    PenaltyType.BAN_7D: 7 * 24,
    PenaltyType.BAN_PERMANENT: None,         # 永久
    PenaltyType.BAN_PERMANENT_DEVICE: None,  # 永久
}


# ---------------------------------------------------------------------------
# penalty_records — 处罚记录表
# ---------------------------------------------------------------------------

class PenaltyRecord(Base, UUIDMixin, TimestampMixin):
    """处罚记录表。

    记录用户的所有处罚历史，支持处罚梯度计算和申诉。

    设计要点：
    - 每次处罚生成一条记录
    - 支持申诉状态跟踪
    - 记录处罚原因和证据
    """

    __tablename__ = "penalty_records"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        comment="被处罚用户ID",
    )
    violation_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="违规类型",
    )
    violation_severity: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="违规程度：minor/moderate/severe",
    )
    penalty_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="处罚类型",
    )
    penalty_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False,
        comment="该违规类型的累计次数",
    )
    reason: Mapped[str | None] = mapped_column(
        String(500),
        comment="处罚原因描述",
    )
    evidence: Mapped[str | None] = mapped_column(
        Text,
        comment="证据（JSON格式，如消息ID、举报ID等）",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        comment="处罚结束时间（null表示永久）",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False,
        comment="处罚是否生效中",
    )
    appeal_status: Mapped[str | None] = mapped_column(
        String(20),
        comment="申诉状态：pending/approved/rejected",
    )
    appeal_reason: Mapped[str | None] = mapped_column(
        String(500),
        comment="申诉理由",
    )
    reviewed_by: Mapped[str | None] = mapped_column(
        CHAR(36),
        comment="审核管理员ID",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        comment="审核时间",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(
        back_populates="penalty_records",
        lazy="noload",
    )

    __table_args__ = (
        Index("idx_penalty_records_user_id", "user_id"),
        Index("idx_penalty_records_violation_type", "violation_type"),
        Index("idx_penalty_records_is_active", "is_active"),
        Index("idx_penalty_records_created", "created_at"),
        Index("idx_penalty_records_appeal_status", "appeal_status"),
    )


# ---------------------------------------------------------------------------
# device_bans — 设备封禁表
# ---------------------------------------------------------------------------

class DeviceBan(Base, UUIDMixin, TimestampMixin):
    """设备封禁表。

    记录被永久封禁的设备，用于防止换号注册。

    设计要点：
    - 基于设备指纹识别
    - 支持多设备关联同一用户
    """

    __tablename__ = "device_bans"

    device_fingerprint: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False,
        comment="设备指纹（用于识别设备）",
    )
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="SET NULL"),
        comment="关联用户ID（用户删除后可能为null）",
    )
    ban_reason: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="封禁原因",
    )
    related_penalty_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("penalty_records.id", ondelete="SET NULL"),
        comment="关联的处罚记录ID",
    )

    __table_args__ = (
        Index("idx_device_bans_fingerprint", "device_fingerprint"),
        Index("idx_device_bans_user_id", "user_id"),
    )
