"""树洞相关模型：树洞帖子、树洞评论。"""

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# treehole_posts — 树洞吐槽表
# ---------------------------------------------------------------------------

class TreeholePost(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """树洞吐槽表。

    用户以匿名身份发布的树洞内容，支持图片、话题标签。
    帖子可设置过期时间，过期后自动隐藏。

    安全设计（PRD 7.5 匿名身份架构隔离）：
    - encrypted_user_id: 加密存储的用户ID，用于软删除和统计
    - 仅通过 anon_identity_id 关联内容，API 返回不暴露真实身份
    """

    __tablename__ = "treehole_posts"

    # 加密存储的用户ID，满足匿名隔离要求
    encrypted_user_id: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="加密的用户ID（AES-256-GCM）",
    )
    anon_identity_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("anonymous_identities.id", ondelete="SET NULL"), comment="匿名身份ID",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="帖子内容",
    )
    topic_tag: Mapped[str | None] = mapped_column(
        String(50), comment="话题标签",
    )
    image_urls: Mapped[list[str] | None] = mapped_column(
        comment="图片URL列表（JSON）",
    )
    resonance_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="共鸣数",
    )
    comment_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="评论数",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active", comment="状态：active/expired/deleted",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="过期时间",
    )

    # ---- 关系 ----
    # 移除直接用户关系，仅通过匿名身份关联（匿名隔离）
    anon_identity: Mapped["AnonymousIdentity"] = relationship(back_populates="treehole_posts")
    comments: Mapped[list["TreeholeComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_treehole_posts_anon_id", "anon_identity_id"),
        Index("idx_treehole_posts_status", "status"),
        Index("idx_treehole_posts_created", "created_at"),
        Index("idx_treehole_posts_topic", "topic_tag"),
    )


# ---------------------------------------------------------------------------
# treehole_comments — 树洞评论表
# ---------------------------------------------------------------------------

class TreeholeComment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """树洞评论表。

    用户对树洞帖子的评论，支持"共鸣"类型（轻量互动）。
    内容限制 100 字以保持轻量。

    安全设计（PRD 7.5 匿名身份架构隔离）：
    - 仅存储 anon_identity_id，不存储 user_id
    - 评论完全匿名化，无法追溯真实用户
    """

    __tablename__ = "treehole_comments"

    post_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("treehole_posts.id", ondelete="CASCADE"), nullable=False, comment="帖子ID",
    )
    anon_identity_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("anonymous_identities.id", ondelete="SET NULL"), comment="匿名身份ID",
    )
    content: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="评论内容，限制100字",
    )
    is_resonance: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否为共鸣（轻量互动）",
    )

    # ---- 关系 ----
    post: Mapped["TreeholePost"] = relationship(back_populates="comments")
    anon_identity: Mapped["AnonymousIdentity"] = relationship(back_populates="treehole_comments")

    __table_args__ = (
        Index("idx_treehole_comments_post_id", "post_id"),
        Index("idx_treehole_comments_anon_id", "anon_identity_id"),
        Index("idx_treehole_comments_created", "created_at"),
    )
