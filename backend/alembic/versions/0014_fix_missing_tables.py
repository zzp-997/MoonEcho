"""修复缺失的 user_events 表

Revision ID: 0014
Revises: 0013_posts_tables
Create Date: 2026-05-06

修复内容：
1. user_events 表 - 模型中定义但迁移中缺失

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ----------------------------------------------------------
    # user_events — 用户行为事件表
    # ----------------------------------------------------------
    if not inspector.has_table("user_events"):
        op.create_table(
            "user_events",
            sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
            sa.Column(
                "user_id",
                sa.CHAR(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="用户ID",
            ),
            sa.Column(
                "event_type",
                sa.String(50),
                nullable=False,
                comment="事件类型：diary_created/ai_chat_message/friend_request_sent 等",
            ),
            sa.Column(
                "event_data",
                sa.JSON,
                nullable=True,
                comment="事件附加数据（JSON），不同事件类型携带不同数据结构",
            ),
            sa.Column(
                "source",
                sa.String(20),
                nullable=True,
                comment="事件来源：app/web/mini_program",
            ),
            sa.Column(
                "created_at",
                sa.DateTime,
                server_default=sa.func.now(),
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                comment="更新时间",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        # 用户维度查询：按用户筛选事件
        op.create_index("idx_user_events_user_id", "user_events", ["user_id"])
        # 事件类型维度查询：按事件类型筛选
        op.create_index("idx_user_events_event_type", "user_events", ["event_type"])
        # 联合查询：按用户+事件类型组合筛选（统计模块高频查询）
        op.create_index("idx_user_events_user_type", "user_events", ["user_id", "event_type"])
        # 时间范围查询：按事件发生时间筛选（支持时间窗口统计）
        op.create_index("idx_user_events_created_at", "user_events", ["created_at"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if inspector.has_table("user_events"):
        op.drop_index("idx_user_events_created_at", "user_events")
        op.drop_index("idx_user_events_user_type", "user_events")
        op.drop_index("idx_user_events_event_type", "user_events")
        op.drop_index("idx_user_events_user_id", "user_events")
        op.drop_table("user_events")
