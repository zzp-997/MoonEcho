"""用户封禁和青少年模式相关字段

Revision ID: 0006_user_ban_fields
Revises: 0005_holidays
Create Date: 2026-04-26

为 users 表添加封禁和青少年模式相关字段：
- is_banned: 是否被封禁
- ban_reason: 封禁原因
- ban_until: 封禁结束时间
- guardian_phone: 监护人手机号

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_user_ban_fields"
down_revision: Union[str, None] = "0005_holidays"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为 users 表添加封禁和青少年模式相关字段。"""

    # ----------------------------------------------------------
    # 添加封禁相关字段
    # ----------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("is_banned", sa.Boolean, default=False, server_default="0", comment="是否被封禁"),
    )
    op.add_column(
        "users",
        sa.Column("ban_reason", sa.String(500), comment="封禁原因"),
    )
    op.add_column(
        "users",
        sa.Column("ban_until", sa.DateTime, comment="封禁结束时间（null表示永久封禁）"),
    )

    # ----------------------------------------------------------
    # 添加青少年模式监护人字段
    # ----------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("guardian_phone", sa.String(20), comment="监护人手机号"),
    )

    # ----------------------------------------------------------
    # 创建索引以提高查询性能
    # ----------------------------------------------------------
    op.create_index("idx_users_is_banned", "users", ["is_banned"])
    op.create_index("idx_users_is_minor", "users", ["is_minor"])


def downgrade() -> None:
    """删除封禁和青少年模式相关字段。"""
    op.drop_index("idx_users_is_minor", "users")
    op.drop_index("idx_users_is_banned", "users")
    op.drop_column("users", "guardian_phone")
    op.drop_column("users", "ban_until")
    op.drop_column("users", "ban_reason")
    op.drop_column("users", "is_banned")
