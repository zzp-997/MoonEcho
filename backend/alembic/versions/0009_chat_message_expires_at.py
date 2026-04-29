"""消息过期字段

Revision ID: 0009_chat_message_expires_at
Revises: 0008_friend_system
Create Date: 2026-04-29

为 chat_messages 表添加 expires_at 字段，用于图片消息的90天过期机制。

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0009_chat_message_expires_at"
down_revision: Union[str, None] = "0008_friend_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为 chat_messages 表添加 expires_at 字段。"""

    # 使用 batch_alter_table 以兼容 SQLite
    with op.batch_alter_table("chat_messages", schema=None) as batch_op:
        # 添加 expires_at 字段（图片消息90天过期）
        batch_op.add_column(
            sa.Column("expires_at", sa.DateTime, comment="过期时间（图片消息90天后过期）"),
        )
        # 添加索引以提高过期消息查询效率
        batch_op.create_index("idx_chat_messages_expires_at", ["expires_at"])


def downgrade() -> None:
    """移除 expires_at 字段。"""

    with op.batch_alter_table("chat_messages", schema=None) as batch_op:
        batch_op.drop_index("idx_chat_messages_expires_at")
        batch_op.drop_column("expires_at")
