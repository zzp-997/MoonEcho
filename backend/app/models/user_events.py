"""用户行为事件模型：记录用户关键行为事件，为数据统计与等级/成就系统提供事件源。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class UserEvent(Base, UUIDMixin, TimestampMixin):
    """用户行为事件表。

    记录用户在 APP 中的关键行为事件，支持数据统计分析和等级/成就系统的事件触发。
    典型事件类型包括：
    - diary_created: 创建情绪日记
    - ai_chat_message: AI 对话消息
    - friend_request_sent: 发送好友请求
    - post_created: 创建动态
    - treehole_post_created: 发布树洞帖子
    - login: 用户登录
    - resonance_given: 给予共鸣
    - comment_created: 创建评论
    event_data 为 JSON 类型，存储事件附加数据，不同事件类型携带不同的数据结构。
    """

    __tablename__ = "user_events"

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="事件类型：diary_created/ai_chat_message/friend_request_sent 等",
    )
    event_data: Mapped[dict[str, Any] | None] = mapped_column(
        comment="事件附加数据（JSON），不同事件类型携带不同数据结构",
    )
    source: Mapped[str | None] = mapped_column(
        String(20),
        comment="事件来源：app/web/mini_program",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="user_events")

    __table_args__ = (
        # 用户维度查询：按用户筛选事件
        Index("idx_user_events_user_id", "user_id"),
        # 事件类型维度查询：按事件类型筛选
        Index("idx_user_events_event_type", "event_type"),
        # 联合查询：按用户+事件类型组合筛选（统计模块高频查询）
        Index("idx_user_events_user_type", "user_id", "event_type"),
        # 时间范围查询：按事件发生时间筛选（支持时间窗口统计）
        Index("idx_user_events_created_at", "created_at"),
    )
