"""管理后台相关模型：管理员、操作日志。"""

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
# admins — 管理员表
# ---------------------------------------------------------------------------

class Admin(Base, UUIDMixin, TimestampMixin):
    """管理员表。

    系统管理员账户，支持角色权限管理。
    密码使用 bcrypt 加密存储。
    """

    __tablename__ = "admins"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="用户名",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希（bcrypt）",
    )
    nickname: Mapped[str | None] = mapped_column(
        String(50), comment="昵称",
    )
    role: Mapped[str] = mapped_column(
        String(20), default="admin", server_default="admin", comment="角色：super_admin/admin/operator",
    )
    permissions: Mapped[dict[str, Any] | None] = mapped_column(
        comment="权限列表（JSON），如 {'user': ['read', 'write'], 'content': ['read']}",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后登录时间",
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45), comment="最后登录IP",
    )

    # ---- 关系 ----
    logs: Mapped[list["AdminLog"]] = relationship(
        back_populates="admin", cascade="all, delete-orphan", lazy="noload",
    )

    __table_args__ = (
        Index("idx_admins_username", "username"),
        Index("idx_admins_role", "role"),
        Index("idx_admins_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# admin_logs — 操作日志表
# ---------------------------------------------------------------------------

class AdminLog(Base, UUIDMixin, TimestampMixin):
    """操作日志表。

    记录管理员操作行为，用于审计追溯。
    """

    __tablename__ = "admin_logs"

    admin_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("admins.id", ondelete="CASCADE"), nullable=False, comment="管理员ID",
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="操作类型：login/logout/create/update/delete/export 等",
    )
    target_type: Mapped[str | None] = mapped_column(
        String(50), comment="操作对象类型：user/post/comment/report 等",
    )
    target_id: Mapped[str | None] = mapped_column(
        CHAR(36), comment="操作对象ID",
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(
        comment="操作详情（JSON）",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), comment="操作IP",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500), comment="浏览器User-Agent",
    )

    # ---- 关系 ----
    admin: Mapped["Admin"] = relationship(back_populates="logs")

    __table_args__ = (
        Index("idx_admin_logs_admin_id", "admin_id"),
        Index("idx_admin_logs_action", "action"),
        Index("idx_admin_logs_target", "target_type", "target_id"),
        Index("idx_admin_logs_created", "created_at"),
    )
