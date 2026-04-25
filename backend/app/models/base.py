"""SQLAlchemy 模型基类和通用 Mixin 定义。

提供所有 ORM 模型共享的基础设施：
- Base: DeclarativeBase，所有模型的声明基类
- UUIDMixin: UUID 主键（CHAR(36)，应用层生成），符合 MySQL 8.0 迁移方案
- TimestampMixin: created_at / updated_at 自动时间戳
- SoftDeleteMixin: is_active / deleted_at 软删除支持
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CHAR, DateTime, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。

    所有 ORM 模型必须继承此类。
    不在此处定义公共列，而是通过 Mixin 按需组合。
    """

    # 类型注解映射：dict 和 list 类型自动映射为 JSON 列类型
    type_annotation_map = {
        dict[str, Any]: JSON,
        list[str]: JSON,
        list[Any]: JSON,
    }


class UUIDMixin:
    """UUID 主键 Mixin。

    使用 CHAR(36) 存储应用层生成的 UUID，符合技术架构中 MySQL 8.0 的迁移方案
    （MySQL 不支持原生 UUID 类型，使用应用层生成 + CHAR(36) 存储）。
    """

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键UUID，应用层生成",
    )


class TimestampMixin:
    """时间戳 Mixin。

    自动管理 created_at 和 updated_at 字段，
    使用 server_default 与 onupdate 确保数据库层面的一致性。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        default=func.now(),
        comment="更新时间",
    )


class SoftDeleteMixin:
    """软删除 Mixin。

    提供 is_active 标记和 deleted_at 时间戳，
    删除操作通过设置 is_active=False + deleted_at=now() 实现，
    避免物理删除导致的数据不可恢复问题。
    """

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        comment="是否有效：True=有效，False=已删除",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="删除时间，软删除时记录",
    )
