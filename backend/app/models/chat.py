"""聊天相关模型：好友申请、好友关系、会话、私聊消息。"""

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
# friend_requests — 好友申请表
# ---------------------------------------------------------------------------
# 设计要点：
# 1. 申请状态独立管理，支持过期机制
# 2. 记录申请次数，支持30天内最多3次的限制
# 3. 支持冷却期机制（过期后24小时冷却）
# ---------------------------------------------------------------------------

class FriendRequest(Base, UUIDMixin, TimestampMixin):
    """好友申请表。

    存储好友申请记录，支持：
    - 申请状态管理（pending/accepted/rejected/expired）
    - 7天过期机制
    - 过期后24小时冷却期
    - 同一用户30天最多发送3次申请
    """

    __tablename__ = "friend_requests"

    sender_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发送者用户ID",
    )
    recipient_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="接收者用户ID",
    )
    greeting_message: Mapped[str | None] = mapped_column(
        String(200), comment="打招呼语",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", comment="状态：pending/accepted/rejected/expired",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="过期时间（申请发送后7天）",
    )
    handled_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="处理时间（同意/忽略时）",
    )
    request_number: Mapped[int] = mapped_column(
        default=1, server_default="1", comment="申请序号（同一用户对的第几次申请）",
    )

    # ---- 关系 ----
    sender: Mapped["User"] = relationship(
        back_populates="sent_friend_requests",
        foreign_keys=[sender_id],
    )
    recipient: Mapped["User"] = relationship(
        back_populates="received_friend_requests",
        foreign_keys=[recipient_id],
    )

    __table_args__ = (
        UniqueConstraint("sender_id", "recipient_id", "request_number", name="uk_friend_requests_sender_recipient_number"),
        Index("idx_friend_requests_sender_id", "sender_id"),
        Index("idx_friend_requests_recipient_id", "recipient_id"),
        Index("idx_friend_requests_status", "status"),
        Index("idx_friend_requests_expires_at", "expires_at"),
    )


# ---------------------------------------------------------------------------
# friendships — 好友关系表
# ---------------------------------------------------------------------------
# 设计要点：
# 1. 使用 user_id_1 < user_id_2 的方式存储，确保关系唯一性
# 2. 好友关系建立后创建会话
# 3. 支持删除好友（软删除，保留聊天记录但无法发送消息）
# ---------------------------------------------------------------------------

class Friendship(Base, UUIDMixin, TimestampMixin):
    """好友关系表。

    存储已建立的好友关系，支持：
    - 双向好友关系（使用较小的 ID 作为 user_id_1）
    - 好友删除（软删除，保留聊天记录）
    """

    __tablename__ = "friendships"

    # 使用较小的 ID 作为 user_id_1，确保无向图存储一致性
    user_id_1: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较小者）",
    )
    user_id_2: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（较大者）",
    )
    request_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("friend_requests.id", ondelete="SET NULL"), comment="关联的好友申请ID",
    )

    # ---- 关系 ----
    # 注意：user_id_1 和 user_id_2 的关系通过 Conversation 间接使用
    # 这里不定义反向关系，避免复杂性

    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="uk_friendships_user_pair"),
        Index("idx_friendships_user_id_1", "user_id_1"),
        Index("idx_friendships_user_id_2", "user_id_2"),
    )


# ---------------------------------------------------------------------------
# user_blocks — 用户拉黑表
# ---------------------------------------------------------------------------
# 设计要点：
# 1. 拉黑后对方无法查看你的动态和主页
# 2. 无法发送好友申请
# 3. 聊天记录从双方的聊天列表中消失
# ---------------------------------------------------------------------------

class UserBlock(Base, UUIDMixin, TimestampMixin):
    """用户拉黑表。

    存储用户拉黑关系，支持：
    - 拉黑后对方无法查看动态和主页
    - 拉黑后无法发送好友申请
    - 聊天记录从双方聊天列表消失
    """

    __tablename__ = "user_blocks"

    blocker_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="拉黑者用户ID",
    )
    blocked_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="被拉黑者用户ID",
    )
    reason: Mapped[str | None] = mapped_column(
        String(200), comment="拉黑原因（可选）",
    )

    # ---- 关系 ----
    blocker: Mapped["User"] = relationship(
        back_populates="blocked_users",
        foreign_keys=[blocker_id],
    )
    blocked: Mapped["User"] = relationship(
        back_populates="blocked_by_users",
        foreign_keys=[blocked_id],
    )

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uk_user_blocks_blocker_blocked"),
        Index("idx_user_blocks_blocker_id", "blocker_id"),
        Index("idx_user_blocks_blocked_id", "blocked_id"),
    )


# ---------------------------------------------------------------------------
# conversations — 会话表
# ---------------------------------------------------------------------------
# 设计要点：
# 1. 好友关系建立后自动创建会话
# 2. 记录最后消息时间和预览
# 3. 删除好友后会话保留但无法发送消息
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
# 设计要点：
# 1. 存储会话中的消息记录
# 2. 支持多种消息类型
# 3. 支持已读状态
# ---------------------------------------------------------------------------

class ChatMessage(Base, UUIDMixin, TimestampMixin):
    """私聊消息表。

    存储会话中的消息记录，支持多种消息类型。
    图片消息支持90天自动过期。
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
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="过期时间（图片消息90天后过期）",
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
        Index("idx_chat_messages_expires_at", "expires_at"),
    )