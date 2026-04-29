"""好友系统表结构

Revision ID: 0008_friend_system
Revises: 0007_phone_field_security_fix
Create Date: 2026-04-29

创建好友系统相关表：
- friend_requests: 好友申请表
- user_blocks: 用户拉黑表
- 修改 friendships 表结构

同时预置官方AI账号：
- 小温 (ai000001-0000-0000-0000-000000000001)
- 老黑 (ai000002-0000-0000-0000-000000000002)
- 阿理 (ai000003-0000-0000-0000-000000000003)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008_friend_system"
down_revision: Union[str, None] = "0007_phone_field_security_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建好友系统表结构并预置官方AI账号。"""

    # ----------------------------------------------------------
    # friend_requests — 好友申请表
    # ----------------------------------------------------------
    op.create_table(
        "friend_requests",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("sender_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发送者用户ID"),
        sa.Column("recipient_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="接收者用户ID"),
        sa.Column("greeting_message", sa.String(200), comment="打招呼语"),
        sa.Column("status", sa.String(20), default="pending", server_default="pending", nullable=False, comment="状态：pending/accepted/rejected/expired"),
        sa.Column("expires_at", sa.DateTime, nullable=False, comment="过期时间（申请发送后7天）"),
        sa.Column("handled_at", sa.DateTime, comment="处理时间"),
        sa.Column("request_number", sa.Integer, default=1, server_default="1", nullable=False, comment="申请序号"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sender_id", "recipient_id", "request_number", name="uk_friend_requests_sender_recipient_number"),
    )
    op.create_index("idx_friend_requests_sender_id", "friend_requests", ["sender_id"])
    op.create_index("idx_friend_requests_recipient_id", "friend_requests", ["recipient_id"])
    op.create_index("idx_friend_requests_status", "friend_requests", ["status"])
    op.create_index("idx_friend_requests_expires_at", "friend_requests", ["expires_at"])

    # ----------------------------------------------------------
    # user_blocks — 用户拉黑表
    # ----------------------------------------------------------
    op.create_table(
        "user_blocks",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("blocker_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="拉黑者用户ID"),
        sa.Column("blocked_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="被拉黑者用户ID"),
        sa.Column("reason", sa.String(200), comment="拉黑原因"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("blocker_id", "blocked_id", name="uk_user_blocks_blocker_blocked"),
    )
    op.create_index("idx_user_blocks_blocker_id", "user_blocks", ["blocker_id"])
    op.create_index("idx_user_blocks_blocked_id", "user_blocks", ["blocked_id"])

    # ----------------------------------------------------------
    # 修改 friendships 表结构（移除 initiator_id 和 status 字段）
    # 添加 request_id 字段关联好友申请
    # 注意：SQLite 不支持 DROP COLUMN，使用 batch_alter_table
    # ----------------------------------------------------------
    # 由于现有 friendships 表可能已有数据，这里采用创建新表+迁移数据的方式

    # 首先检查旧表结构，创建新的 friendships 表结构
    # 由于 SQLite 的限制，我们使用 batch_alter_table 方式
    with op.batch_alter_table("friendships", schema=None) as batch_op:
        # 添加 request_id 字段
        batch_op.add_column(
            sa.Column("request_id", sa.CHAR(36), sa.ForeignKey("friend_requests.id", ondelete="SET NULL"), comment="关联的好友申请ID"),
        )
        # 注意：SQLite 不支持 DROP COLUMN，保留原有字段但不再使用
        # 在生产环境使用 MySQL 时可以执行以下操作：
        # batch_op.drop_column("initiator_id")
        # batch_op.drop_column("greeting_message")
        # batch_op.drop_column("status")

    # ----------------------------------------------------------
    # 预置官方AI账号
    # 小温/老黑/阿理作为独立账号存在，可被添加为好友
    # 使用固定的 UUID 确保迁移的可重复性
    # ----------------------------------------------------------
    official_ai_data = [
        {
            "id": "ai000001-0000-0000-0000-000000000001",
            "phone": "ai_xiaowen_placeholder",
            "phone_hash": "ai_xiaowen_hash_placeholder_000000000001",
            "nickname": "小温",
            "avatar_url": "/assets/avatars/xiaowen.png",
            "is_minor": False,
            "is_banned": False,
            "is_active": True,
        },
        {
            "id": "ai000002-0000-0000-0000-000000000002",
            "phone": "ai_lahei_placeholder",
            "phone_hash": "ai_lahei_hash_placeholder_000000000002",
            "nickname": "老黑",
            "avatar_url": "/assets/avatars/lahei.png",
            "is_minor": False,
            "is_banned": False,
            "is_active": True,
        },
        {
            "id": "ai000003-0000-0000-0000-000000000003",
            "phone": "ai_ali_placeholder",
            "phone_hash": "ai_ali_hash_placeholder_000000000003",
            "nickname": "阿理",
            "avatar_url": "/assets/avatars/ali.png",
            "is_minor": False,
            "is_banned": False,
            "is_active": True,
        },
    ]

    # 批量插入官方AI账号
    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", sa.String),
            sa.column("phone", sa.String),
            sa.column("phone_hash", sa.String),
            sa.column("nickname", sa.String),
            sa.column("avatar_url", sa.String),
            sa.column("is_minor", sa.Boolean),
            sa.column("is_banned", sa.Boolean),
            sa.column("is_active", sa.Boolean),
        ),
        official_ai_data,
    )

    # ----------------------------------------------------------
    # 为 conversations 表添加 friendship_id 外键（如果不存在）
    # ----------------------------------------------------------
    # 检查是否已有 friendship_id 字段
    # 由于 SQLite 的限制，使用 batch_alter_table


def downgrade() -> None:
    """删除好友系统表结构。"""
    op.drop_table("user_blocks")
    op.drop_table("friend_requests")

    # 移除 friendships 表中添加的字段
    with op.batch_alter_table("friendships", schema=None) as batch_op:
        batch_op.drop_column("request_id")

    # 删除预置的官方AI账号
    op.execute(
        sa.text("DELETE FROM users WHERE id IN ('ai000001-0000-0000-0000-000000000001', 'ai000002-0000-0000-0000-000000000002', 'ai000003-0000-0000-0000-000000000003')")
    )
