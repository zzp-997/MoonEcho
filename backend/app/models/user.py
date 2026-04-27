"""用户相关模型：用户表、用户画像标签、匿名身份、用户-匿名身份映射。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CHAR,
    DECIMAL,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# users — 用户表
# ---------------------------------------------------------------------------

class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """用户表。

    存储用户核心信息，包括认证字段、画像属性和社交能量值。
    手机号通过 phone_hash 建立唯一索引，支持按哈希快速查找。

    安全设计：
    - phone 字段存储 AES-256-GCM 加密后的手机号，每次加密结果不同
    - phone 字段不再有唯一约束（密文不可比较）
    - phone_hash 字段存储 HMAC-SHA256 哈希值，用于唯一性校验
    - phone 字段长度扩大到 200 字节以容纳加密后的密文
    """

    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="手机号（AES-256-GCM 加密）",
    )
    phone_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="手机号哈希（用于唯一索引）",
    )
    nickname: Mapped[str | None] = mapped_column(
        String(50), comment="昵称",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), comment="头像URL",
    )
    age_range: Mapped[str | None] = mapped_column(
        String(10), comment="年龄段：18-24/25-30/31-40/40+",
    )
    city: Mapped[str | None] = mapped_column(
        String(50), comment="所在城市",
    )
    occupation: Mapped[str | None] = mapped_column(
        String(50), comment="职业",
    )
    notification_settings: Mapped[dict[str, Any] | None] = mapped_column(
        comment="通知偏好设置（JSON）",
    )
    is_minor: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否未成年人",
    )
    guardian_phone: Mapped[str | None] = mapped_column(
        String(20), comment="监护人手机号",
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否被封禁",
    )
    ban_reason: Mapped[str | None] = mapped_column(
        String(500), comment="封禁原因",
    )
    ban_until: Mapped[datetime | None] = mapped_column(
        DateTime, comment="封禁结束时间（null表示永久封禁）",
    )
    social_energy: Mapped[Decimal | None] = mapped_column(
        DECIMAL(5, 2), default=None, comment="社交能量值 0.00~100.00",
    )
    social_energy_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, comment="社交能量最后更新时间",
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, comment="最后活跃时间",
    )

    # ---- 关系 ----
    tags: Mapped[list["UserTag"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
    )
    anonymous_identities: Mapped[list["AnonymousIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
    )
    emotion_diaries: Mapped[list["EmotionDiary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )
    treehole_posts: Mapped[list["TreeholePost"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )
    square_posts: Mapped[list["Post"]] = relationship(
        back_populates="anon_identity", cascade="all, delete-orphan", lazy="noload",
        foreign_keys="Post.anon_identity_id",
    )
    initiated_friendships: Mapped[list["Friendship"]] = relationship(
        back_populates="initiator",
        foreign_keys="Friendship.initiator_id",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    received_friendships: Mapped[list["Friendship"]] = relationship(
        back_populates="recipient",
        foreign_keys="Friendship.recipient_id",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    ai_conversations: Mapped[list["AIConversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )
    weekly_reports: Mapped[list["WeeklyReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )
    user_holidays: Mapped[list["UserHoliday"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_users_phone_hash", "phone_hash"),
        Index("idx_users_created", "created_at"),
        Index("idx_users_last_active", "last_active_at"),
        Index("idx_users_is_active", "is_active"),
        Index("idx_users_is_banned", "is_banned"),
        Index("idx_users_is_minor", "is_minor"),
    )


# ---------------------------------------------------------------------------
# user_tags — 用户画像标签表
# ---------------------------------------------------------------------------

class UserTag(Base, UUIDMixin, TimestampMixin):
    """用户画像标签表。

    每条记录代表用户的一个标签，通过 tag_key 区分标签类型。
    同一用户同一 tag_key 只能有一条记录（唯一约束）。
    """

    __tablename__ = "user_tags"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    tag_key: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="标签键，如 interest、personality",
    )
    tag_value: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="标签值",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="tags")

    __table_args__ = (
        UniqueConstraint("user_id", "tag_key", name="uk_user_tags_user_tag_key"),
        Index("idx_user_tags_user_id", "user_id"),
        Index("idx_user_tags_tag_key", "tag_key"),
    )


# ---------------------------------------------------------------------------
# anonymous_identities — 匿名身份表
# ---------------------------------------------------------------------------

class AnonymousIdentity(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """匿名身份表。

    每个用户可以拥有多个匿名身份，用于在不同场景下隔离真实身份。
    匿名身份包含独立的昵称和头像，用于树洞、广场等场景。
    """

    __tablename__ = "anonymous_identities"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    anon_nickname: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="匿名昵称",
    )
    anon_avatar_url: Mapped[str | None] = mapped_column(
        String(500), comment="匿名头像URL",
    )
    persona_type: Mapped[str | None] = mapped_column(
        String(30), comment="人设类型：listener/venter/thinker 等",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="anonymous_identities")
    mapping: Mapped["UserAnonMapping"] = relationship(
        back_populates="anonymous_identity", cascade="all, delete-orphan", uselist=False,
    )
    treehole_posts: Mapped[list["TreeholePost"]] = relationship(
        back_populates="anon_identity", lazy="noload",
    )
    square_posts: Mapped[list["Post"]] = relationship(
        back_populates="anon_identity", lazy="noload",
    )

    __table_args__ = (
        Index("idx_anon_identities_user_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# user_anon_mapping — 用户-匿名身份映射表
# ---------------------------------------------------------------------------

class UserAnonMapping(Base, UUIDMixin, TimestampMixin):
    """用户-匿名身份映射表。

    记录用户与匿名身份的绑定关系，一个用户在同一场景下只使用一个匿名身份。
    唯一约束确保同一用户在同一场景下不会重复绑定。
    """

    __tablename__ = "user_anon_mapping"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    anon_identity_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("anonymous_identities.id", ondelete="CASCADE"), nullable=False, comment="匿名身份ID",
    )
    scene: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="使用场景：treehole/square/chat",
    )

    # ---- 关系 ----
    anonymous_identity: Mapped["AnonymousIdentity"] = relationship(back_populates="mapping")

    __table_args__ = (
        UniqueConstraint("user_id", "scene", name="uk_user_anon_mapping_user_scene"),
        Index("idx_user_anon_mapping_user_id", "user_id"),
        Index("idx_user_anon_mapping_anon_id", "anon_identity_id"),
    )
