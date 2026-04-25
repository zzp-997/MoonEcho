"""动态广场相关模型：动态帖子表。"""

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


class Post(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """动态广场表。

    用户发布的动态帖子，支持匿名/实名发布和可见性控制。
    """

    __tablename__ = "posts"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="动态内容",
    )
    image_urls: Mapped[list[str] | None] = mapped_column(
        comment="图片URL列表（JSON）",
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否匿名发布",
    )
    visibility: Mapped[str] = mapped_column(
        String(20), default="public", server_default="public", comment="可见性：public/friends/private",
    )
    like_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="点赞数",
    )
    comment_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="评论数",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="posts")

    __table_args__ = (
        Index("idx_posts_user_id", "user_id"),
        Index("idx_posts_created", "created_at"),
        Index("idx_posts_visibility", "visibility"),
        Index("idx_posts_is_active", "is_active"),
    )
