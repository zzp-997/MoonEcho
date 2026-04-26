"""修复 phone 字段安全设计问题

Revision ID: 0007_phone_field_security_fix
Revises: 0006_user_ban_fields
Create Date: 2026-04-26

修复内容：
1. 移除 users 表 phone 字段的唯一约束（密文每次加密结果不同，不可比较）
2. 增加 phone 字段长度从 20 到 200 字节（AES-256-GCM 加密后密文更长）
3. 确保 phone_hash 字段有唯一约束（用于唯一性校验）

背景：
- phone 字段存储 AES-256-GCM 加密后的手机号
- 每次加密同一明文产生不同密文（由于随机 nonce）
- 原有 unique=True 约束会导致同一手机号无法重新注册
- 密文长度约 56-60 字节（Base64 编码后），需增加字段长度

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007_phone_field_security_fix"
down_revision: Union[str, None] = "0006_user_ban_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """修复 phone 字段设计问题。"""

    # SQLite 不支持直接 ALTER COLUMN，需要重建表
    # 对于 MySQL/PostgreSQL 可以直接执行：
    # op.drop_constraint("users_phone_key", "users", type_="unique")
    # op.alter_column("users", "phone", type_=sa.String(200))

    # 获取数据库类型
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # SQLite 需要重建表
        _upgrade_sqlite()
    else:
        # MySQL/PostgreSQL 直接修改
        _upgrade_other()


def _upgrade_sqlite() -> None:
    """SQLite 数据库升级（重建表）。"""

    # 1. 创建临时表（新结构）
    op.create_table(
        "users_new",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("phone", sa.String(200), nullable=False, comment="手机号（AES-256-GCM 加密）"),
        sa.Column("phone_hash", sa.String(64), unique=True, nullable=False, comment="手机号哈希（用于唯一索引）"),
        sa.Column("nickname", sa.String(50), comment="昵称"),
        sa.Column("avatar_url", sa.String(500), comment="头像URL"),
        sa.Column("age_range", sa.String(10), comment="年龄段"),
        sa.Column("city", sa.String(50), comment="所在城市"),
        sa.Column("occupation", sa.String(50), comment="职业"),
        sa.Column("notification_settings", sa.JSON, comment="通知偏好设置"),
        sa.Column("is_minor", sa.Boolean, default=False, server_default="0", comment="是否未成年人"),
        sa.Column("guardian_phone", sa.String(200), comment="监护人手机号（加密）"),
        sa.Column("is_banned", sa.Boolean, default=False, server_default="0", comment="是否被封禁"),
        sa.Column("ban_reason", sa.String(500), comment="封禁原因"),
        sa.Column("ban_until", sa.DateTime, comment="封禁结束时间"),
        sa.Column("social_energy", sa.DECIMAL(5, 2), comment="社交能量值"),
        sa.Column("social_energy_updated_at", sa.DateTime, comment="社交能量最后更新时间"),
        sa.Column("last_active_at", sa.DateTime, comment="最后活跃时间"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. 复制数据
    op.execute("""
        INSERT INTO users_new (
            id, phone, phone_hash, nickname, avatar_url, age_range, city, occupation,
            notification_settings, is_minor, guardian_phone, is_banned, ban_reason, ban_until,
            social_energy, social_energy_updated_at, last_active_at,
            is_active, deleted_at, created_at, updated_at
        )
        SELECT
            id, phone, phone_hash, nickname, avatar_url, age_range, city, occupation,
            notification_settings, is_minor, guardian_phone, is_banned, ban_reason, ban_until,
            social_energy, social_energy_updated_at, last_active_at,
            is_active, deleted_at, created_at, updated_at
        FROM users
    """)

    # 3. 删除旧表
    op.drop_table("users")

    # 4. 重命名新表
    op.rename_table("users_new", "users")

    # 5. 重建索引
    op.create_index("idx_users_phone_hash", "users", ["phone_hash"])
    op.create_index("idx_users_created", "users", ["created_at"])
    op.create_index("idx_users_last_active", "users", ["last_active_at"])
    op.create_index("idx_users_is_active", "users", ["is_active"])
    op.create_index("idx_users_is_banned", "users", ["is_banned"])
    op.create_index("idx_users_is_minor", "users", ["is_minor"])


def _upgrade_other() -> None:
    """MySQL/PostgreSQL 数据库升级。"""

    # 移除 phone 字段的唯一约束
    # 约束名可能是 users_phone_key 或 users_phone_unique
    # 尝试常见的约束名
    try:
        op.drop_constraint("users_phone_key", "users", type_="unique")
    except Exception:
        try:
            op.drop_constraint("users_phone_unique", "users", type_="unique")
        except Exception:
            # 如果约束名不同，可能需要手动处理
            pass

    # 修改 phone 字段长度
    op.alter_column(
        "users",
        "phone",
        type_=sa.String(200),
        existing_type=sa.String(20),
        comment="手机号（AES-256-GCM 加密）",
    )

    # 修改 guardian_phone 字段长度（如果存在）
    try:
        op.alter_column(
            "users",
            "guardian_phone",
            type_=sa.String(200),
            existing_type=sa.String(20),
            comment="监护人手机号（加密）",
        )
    except Exception:
        # guardian_phone 字段可能不存在（未应用 0006 迁移）
        pass


def downgrade() -> None:
    """回滚 phone 字段修改。"""

    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        _downgrade_sqlite()
    else:
        _downgrade_other()


def _downgrade_sqlite() -> None:
    """SQLite 数据库降级（重建表）。"""

    # 创建旧结构的表
    op.create_table(
        "users_old",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("phone", sa.String(20), unique=True, nullable=False, comment="手机号"),
        sa.Column("phone_hash", sa.String(64), unique=True, nullable=False, comment="手机号哈希"),
        sa.Column("nickname", sa.String(50), comment="昵称"),
        sa.Column("avatar_url", sa.String(500), comment="头像URL"),
        sa.Column("age_range", sa.String(10), comment="年龄段"),
        sa.Column("city", sa.String(50), comment="所在城市"),
        sa.Column("occupation", sa.String(50), comment="职业"),
        sa.Column("notification_settings", sa.JSON, comment="通知偏好设置"),
        sa.Column("is_minor", sa.Boolean, default=False, server_default="0", comment="是否未成年人"),
        sa.Column("guardian_phone", sa.String(20), comment="监护人手机号"),
        sa.Column("is_banned", sa.Boolean, default=False, server_default="0", comment="是否被封禁"),
        sa.Column("ban_reason", sa.String(500), comment="封禁原因"),
        sa.Column("ban_until", sa.DateTime, comment="封禁结束时间"),
        sa.Column("social_energy", sa.DECIMAL(5, 2), comment="社交能量值"),
        sa.Column("social_energy_updated_at", sa.DateTime, comment="社交能量最后更新时间"),
        sa.Column("last_active_at", sa.DateTime, comment="最后活跃时间"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否有效"),
        sa.Column("deleted_at", sa.DateTime, comment="删除时间"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 复制数据（截断过长的 phone）
    op.execute("""
        INSERT INTO users_old (
            id, phone, phone_hash, nickname, avatar_url, age_range, city, occupation,
            notification_settings, is_minor, guardian_phone, is_banned, ban_reason, ban_until,
            social_energy, social_energy_updated_at, last_active_at,
            is_active, deleted_at, created_at, updated_at
        )
        SELECT
            id, substr(phone, 1, 20), phone_hash, nickname, avatar_url, age_range, city, occupation,
            notification_settings, is_minor, substr(guardian_phone, 1, 20), is_banned, ban_reason, ban_until,
            social_energy, social_energy_updated_at, last_active_at,
            is_active, deleted_at, created_at, updated_at
        FROM users
    """)

    op.drop_table("users")
    op.rename_table("users_old", "users")

    # 重建索引
    op.create_index("idx_users_phone_hash", "users", ["phone_hash"])
    op.create_index("idx_users_created", "users", ["created_at"])
    op.create_index("idx_users_last_active", "users", ["last_active_at"])
    op.create_index("idx_users_is_active", "users", ["is_active"])


def _downgrade_other() -> None:
    """MySQL/PostgreSQL 数据库降级。"""

    # 添加唯一约束
    try:
        op.create_unique_constraint("users_phone_key", "users", ["phone"])
    except Exception:
        pass

    # 恢复字段长度
    op.alter_column(
        "users",
        "phone",
        type_=sa.String(20),
        existing_type=sa.String(200),
    )
