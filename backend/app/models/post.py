"""动态广场相关模型：动态帖子表、动态评论表、动态共鸣/收藏记录表。"""

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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Post(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """动态广场帖子表。

    用户发布的动态帖子，支持匿名/实名发布和可见性控制。

    设计要点：
    - 支持实名/匿名切换：is_anonymous 字段控制
    - 匿名发布使用 anon_identity_id 关联虚拟身份
    - 可见范围设置：visibility 字段（public/friends/private）
    - 匿名动态不可被关注（前端控制，后端不返回用户ID）
    """

    __tablename__ = "posts"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    anon_identity_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("anonymous_identities.id", ondelete="SET NULL"), nullable=True,
        comment="匿名身份ID（匿名发布时使用）",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="动态内容",
    )
    image_urls: Mapped[list[str] | None] = mapped_column(
        comment="图片URL列表（JSON，最多9张）",
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否匿名发布",
    )
    visibility: Mapped[str] = mapped_column(
        String(20), default="public", server_default="public", comment="可见性：public/friends/private",
    )
    like_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="共鸣（点赞）数",
    )
    comment_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="评论数",
    )
    favorite_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="收藏数",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="posts")
    anon_identity: Mapped["AnonymousIdentity | None"] = relationship(
        back_populates="square_posts", lazy="selectin",
    )
    comments: Mapped[list["PostComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_posts_user_id", "user_id"),
        Index("idx_posts_created", "created_at"),
        Index("idx_posts_visibility", "visibility"),
        Index("idx_posts_is_active", "is_active"),
        Index("idx_posts_anon_identity_id", "anon_identity_id"),
    )


class PostComment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """动态评论表。

    支持对动态进行评论互动。
    评论可以设置匿名/实名。
    """

    __tablename__ = "post_comments"

    post_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, comment="动态ID",
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    anon_identity_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("anonymous_identities.id", ondelete="SET NULL"), nullable=True,
        comment="匿名身份ID（匿名评论时使用）",
    )
    content: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="评论内容，最多500字",
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否匿名评论",
    )
    reply_to_comment_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("post_comments.id", ondelete="SET NULL"), nullable=True,
        comment="回复的评论ID（支持评论回复）",
    )

    # ---- 关系 ----
    post: Mapped["Post"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship()
    anon_identity: Mapped["AnonymousIdentity | None"] = relationship(lazy="selectin")
    reply_to_comment: Mapped["PostComment | None"] = relationship(
        back_populates="replies", remote_side="PostComment.id",
    )
    replies: Mapped[list["PostComment"]] = relationship(
        back_populates="reply_to_comment", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_post_comments_post_id", "post_id"),
        Index("idx_post_comments_user_id", "user_id"),
        Index("idx_post_comments_created", "created_at"),
    )


class PostLike(Base, UUIDMixin, TimestampMixin):
    """动态共鸣（点赞）记录表。

    记录用户对动态的共鸣互动。
    每个用户对每条动态只能共鸣一次。
    """

    __tablename__ = "post_likes"

    post_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, comment="动态ID",
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )

    # ---- 关系 ----
    post: Mapped["Post"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uk_post_likes_post_user"),
        Index("idx_post_likes_post_id", "post_id"),
        Index("idx_post_likes_user_id", "user_id"),
    )


class PostFavorite(Base, UUIDMixin, TimestampMixin):
    """动态收藏记录表。

    记录用户收藏的动态。
    每个用户对每条动态只能收藏一次。
    """

    __tablename__ = "post_favorites"

    post_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, comment="动态ID",
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )

    # ---- 关系 ----
    post: Mapped["Post"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uk_post_favorites_post_user"),
        Index("idx_post_favorites_user_id", "user_id"),
    )


class PostFollow(Base, UUIDMixin, TimestampMixin):
    """动态悄悄关注记录表。

    记录用户对发布者的悄悄关注（仅实名动态）。
    被关注者不会收到通知。
    """

    __tablename__ = "post_follows"

    post_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, comment="动态ID",
    )
    follower_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关注者ID",
    )
    following_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="被关注者ID",
    )

    # ---- 关系 ----
    post: Mapped["Post"] = relationship()
    follower: Mapped["User"] = relationship(foreign_keys=[follower_id])
    following: Mapped["User"] = relationship(foreign_keys=[following_id])

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uk_post_follows_follower_following"),
        Index("idx_post_follows_follower_id", "follower_id"),
        Index("idx_post_follows_following_id", "following_id"),
    )
