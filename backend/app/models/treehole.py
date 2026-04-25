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
    """

    __tablename__ = "treehole_posts"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID（真实身份）",
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
    user: Mapped["User"] = relationship(back_populates="treehole_posts")
    anon_identity: Mapped["AnonymousIdentity"] = relationship(back_populates="treehole_posts")
    comments: Mapped[list["TreeholeComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_treehole_posts_user_id", "user_id"),
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
    """

    __tablename__ = "treehole_comments"

    post_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("treehole_posts.id", ondelete="CASCADE"), nullable=False, comment="帖子ID",
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    content: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="评论内容，限制100字",
    )
    is_resonance: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否为共鸣（轻量互动）",
    )

    # ---- 关系 ----
    post: Mapped["TreeholePost"] = relationship(back_populates="comments")

    __table_args__ = (
        Index("idx_treehole_comments_post_id", "post_id"),
        Index("idx_treehole_comments_user_id", "user_id"),
        Index("idx_treehole_comments_created", "created_at"),
    )
