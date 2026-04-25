"""AI 对话相关模型：AI 会话、AI 消息、AI 记忆。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# ai_conversations — AI对话会话表
# ---------------------------------------------------------------------------

class AIConversation(Base, UUIDMixin, TimestampMixin):
    """AI对话会话表。

    用户与 AI 的对话会话，支持不同 AI 人设（小温/老黑/阿理）。
    每个用户可以同时拥有多个不同人设的对话会话。
    """

    __tablename__ = "ai_conversations"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    ai_persona: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="AI人设：xiaowen/laohei/ali",
    )
    title: Mapped[str | None] = mapped_column(
        String(100), comment="会话标题",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否活跃",
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后消息时间",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="ai_conversations")
    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", lazy="noload",
    )
    memories: Mapped[list["AIMemory"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_ai_conversations_user_id", "user_id"),
        Index("idx_ai_conversations_persona", "ai_persona"),
        Index("idx_ai_conversations_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# ai_messages — AI对话消息表
# ---------------------------------------------------------------------------

class AIMessage(Base, UUIDMixin, TimestampMixin):
    """AI对话消息表。

    存储 AI 对话中的消息，区分用户消息和 AI 回复。
    """

    __tablename__ = "ai_messages"

    conversation_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, comment="会话ID",
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="角色：user/assistant",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="消息内容",
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer, comment="token 消耗数",
    )

    # ---- 关系 ----
    conversation: Mapped["AIConversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_ai_messages_conversation_id", "conversation_id"),
        Index("idx_ai_messages_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# ai_memories — AI记忆表
# ---------------------------------------------------------------------------

class AIMemory(Base, UUIDMixin, TimestampMixin):
    """AI记忆表。

    存储 AI 对话中提取的记忆，按类型分级管理。
    短期记忆有时效性（expires_at），长期记忆持续有效。
    importance 用于记忆召回优先级排序。
    """

    __tablename__ = "ai_memories"

    conversation_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("ai_conversations.id", ondelete="SET NULL"), comment="来源会话ID",
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    memory_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="记忆类型：short_term/mid_term/long_term/person_info/event",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="记忆内容",
    )
    key_facts: Mapped[dict[str, Any] | None] = mapped_column(
        comment="关键事实（JSON），结构化提取的信息",
    )
    importance: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5", comment="重要度 1~10",
    )
    source: Mapped[str | None] = mapped_column(
        String(50), comment="来源：chat/diary/behavior",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="过期时间，短期记忆有效",
    )
    access_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="被召回次数",
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后被召回时间",
    )

    # ---- 关系 ----
    conversation: Mapped["AIConversation"] = relationship(back_populates="memories")

    __table_args__ = (
        Index("idx_ai_memories_user_id", "user_id"),
        Index("idx_ai_memories_conversation_id", "conversation_id"),
        Index("idx_ai_memories_type", "memory_type"),
        Index("idx_ai_memories_importance", "importance"),
        Index("idx_ai_memories_expires", "expires_at"),
    )
