"""用户边界设置和勿扰模式

Revision ID: 0010_user_boundary_settings
Revises: 0009_chat_message_expires_at
Create Date: 2026-04-29

添加用户边界设置相关功能：
- user_boundary_settings: 用户边界设置表
- users 表添加 do_not_disturb_until 字段（勿扰模式结束时间）
- users 表添加 auto_dnd_enabled 字段（是否允许自动勿扰）

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0010_user_boundary_settings"
down_revision: Union[str, None] = "0010_penalty_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建用户边界设置表并添加勿扰模式字段。"""

    # ----------------------------------------------------------
    # user_boundary_settings — 用户边界设置表
    # ----------------------------------------------------------
    op.create_table(
        "user_boundary_settings",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        # 消息接收设置
        sa.Column("allow_stranger_messages", sa.Boolean, default=True, server_default="1", nullable=False, comment="是否允许陌生人发消息"),
        sa.Column("require_friend_for_chat", sa.Boolean, default=False, server_default="0", nullable=False, comment="是否需要是好友才能聊天"),
        # 隐私设置
        sa.Column("show_online_status", sa.Boolean, default=False, server_default="0", nullable=False, comment="是否显示在线状态"),
        sa.Column("show_read_status", sa.Boolean, default=True, server_default="1", nullable=False, comment="是否显示已读状态"),
        # 自动保护设置
        sa.Column("auto_block_on_report", sa.Boolean, default=True, server_default="1", nullable=False, comment="举报后自动屏蔽"),
        sa.Column("auto_dnd_on_low_energy", sa.Boolean, default=True, server_default="1", nullable=False, comment="能量耗尽时自动勿扰"),
        sa.Column("dnd_energy_threshold", sa.Integer, default=20, server_default="20", nullable=False, comment="触发自动勿扰的能量阈值"),
        # 安全提示设置
        sa.Column("show_safety_tips", sa.Boolean, default=True, server_default="1", nullable=False, comment="是否显示安全提示"),
        sa.Column("safety_tip_interval_hours", sa.Integer, default=24, server_default="24", nullable=False, comment="安全提示间隔（小时）"),
        # 静默时段设置
        sa.Column("quiet_hours_enabled", sa.Boolean, default=False, server_default="0", nullable=False, comment="是否开启静默时段"),
        sa.Column("quiet_hours_start", sa.String(5), default="22:00", comment="静默时段开始（HH:MM）"),
        sa.Column("quiet_hours_end", sa.String(5), default="07:00", comment="静默时段结束（HH:MM）"),
        # 时间戳
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uk_user_boundary_settings_user_id"),
    )
    op.create_index("idx_user_boundary_settings_user_id", "user_boundary_settings", ["user_id"])

    # ----------------------------------------------------------
    # users 表添加勿扰模式相关字段
    # ----------------------------------------------------------
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("do_not_disturb_until", sa.DateTime, comment="勿扰模式结束时间"),
        )
        batch_op.add_column(
            sa.Column("auto_dnd_enabled", sa.Boolean, default=True, server_default="1", comment="是否允许自动勿扰"),
        )
        batch_op.add_column(
            sa.Column("dnd_energy_threshold", sa.Integer, default=20, server_default="20", comment="触发自动勿扰的能量阈值"),
        )

    op.create_index("idx_users_do_not_disturb", "users", ["do_not_disturb_until"])


def downgrade() -> None:
    """删除用户边界设置表和勿扰模式字段。"""
    op.drop_table("user_boundary_settings")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("do_not_disturb_until")
        batch_op.drop_column("auto_dnd_enabled")
        batch_op.drop_column("dnd_energy_threshold")
