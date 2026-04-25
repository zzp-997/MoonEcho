"""通知相关模型：通知推送、推送记录。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# notifications — 通知推送表
# ---------------------------------------------------------------------------

class Notification(Base, UUIDMixin, TimestampMixin):
    """通知推送表。

    存储用户通知，支持多种通知类型和 payload。
    """

    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="通知类型：friend_request/message/system/ai_reply 等",
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="通知标题",
    )
    content: Mapped[str | None] = mapped_column(
        Text, comment="通知内容",
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(
        comment="附加数据（JSON），如 source_id、action_url 等",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否已读",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="已读时间",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_type", "type"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# push_records — 推送记录表
# ---------------------------------------------------------------------------

class PushRecord(Base, UUIDMixin, TimestampMixin):
    """推送记录表。

    记录推送发送历史，用于推送统计和去重。
    """

    __tablename__ = "push_records"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    notification_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("notifications.id", ondelete="SET NULL"), comment="关联通知ID",
    )
    push_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="推送类型：system/reminder/marketing",
    )
    device_token: Mapped[str | None] = mapped_column(
        String(200), comment="设备推送Token",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", comment="状态：pending/sent/failed",
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="发送时间",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500), comment="错误信息",
    )

    __table_args__ = (
        Index("idx_push_records_user_id", "user_id"),
        Index("idx_push_records_notification_id", "notification_id"),
        Index("idx_push_records_status", "status"),
        Index("idx_push_records_created", "created_at"),
    )
