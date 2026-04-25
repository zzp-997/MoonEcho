"""聊天相关模型：好友关系、会话、私聊消息。"""

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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# friendships — 好友关系表
# ---------------------------------------------------------------------------

class Friendship(Base, UUIDMixin, TimestampMixin):
    """好友关系表。

    存储用户之间的好友关系，支持申请、接受、拒绝状态。
    使用 user_id_1 < user_id_2 的方式存储，确保关系唯一性。
    initiator_id 标识发起方。
    """

    __tablename__ = "friendships"

    # 使用较小的 ID 作为 user_id_1，确保无向图存储一致性
    user_id_1: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较小者）",
    )
    user_id_2: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较大者）",
    )
    initiator_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发起方用户ID",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", comment="状态：pending/accepted/rejected/blocked",
    )
    greeting_message: Mapped[str | None] = mapped_column(
        String(200), comment="好友申请附言",
    )

    # ---- 关系 ----
    initiator: Mapped["User"] = relationship(
        back_populates="initiated_friendships",
        foreign_keys=[initiator_id],
    )
    # 注意：user_id_1 和 user_id_2 的关系通过 Conversation 间接使用
    # 这里不定义反向关系，避免复杂性

    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="uk_friendships_user_pair"),
        Index("idx_friendships_user_id_1", "user_id_1"),
        Index("idx_friendships_user_id_2", "user_id_2"),
        Index("idx_friendships_status", "status"),
        Index("idx_friendships_initiator", "initiator_id"),
    )


# ---------------------------------------------------------------------------
# conversations — 会话表
# ---------------------------------------------------------------------------

class Conversation(Base, UUIDMixin, TimestampMixin):
    """会话表。

    管理用户间的私聊会话，记录最后消息时间和预览。
    与 Friendship 关联，好友关系建立后创建会话。
    """

    __tablename__ = "conversations"

    friendship_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("friendships.id", ondelete="SET NULL"), comment="好友关系ID",
    )
    user_id_1: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较小者）",
    )
    user_id_2: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较大者）",
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后消息时间",
    )
    last_message_preview: Mapped[str | None] = mapped_column(
        String(200), comment="最后消息预览",
    )

    # ---- 关系 ----
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="uk_conversations_user_pair"),
        Index("idx_conversations_user_id_1", "user_id_1"),
        Index("idx_conversations_user_id_2", "user_id_2"),
        Index("idx_conversations_last_message", "last_message_at"),
    )


# ---------------------------------------------------------------------------
# chat_messages — 私聊消息表
# ---------------------------------------------------------------------------

class ChatMessage(Base, UUIDMixin, TimestampMixin):
    """私聊消息表。

    存储会话中的消息记录，支持多种消息类型。
    """

    __tablename__ = "chat_messages"

    conversation_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="会话ID",
    )
    sender_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发送者ID",
    )
    message_type: Mapped[str] = mapped_column(
        String(20), default="text", server_default="text", comment="消息类型：text/image/voice",
    )
    content: Mapped[str | None] = mapped_column(
        Text, comment="消息内容",
    )
    media_url: Mapped[str | None] = mapped_column(
        String(500), comment="媒体文件URL",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否已读",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="已读时间",
    )

    # ---- 关系 ----
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_chat_messages_conversation_id", "conversation_id"),
        Index("idx_chat_messages_sender_id", "sender_id"),
        Index("idx_chat_messages_created", "created_at"),
    )
