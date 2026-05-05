"""添加 ai_messages 表的危机处理字段。

为 AI 消息表添加危机状态、处理人、处理备注和处理时间字段，
用于完整记录危机事件的处理过程。

Revision: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

# revision 标识
revision = "0002"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加危机标记和处理字段。"""
    # 危机级别字段
    op.add_column(
        "ai_messages",
        sa.Column("crisis_level", sa.String(10), nullable=True, comment="危机级别：low/medium/high"),
    )
    # 危机关键词字段
    op.add_column(
        "ai_messages",
        sa.Column("crisis_keywords", sa.String(200), nullable=True, comment="匹配到的危机关键词（逗号分隔）"),
    )
    # 危机状态字段
    op.add_column(
        "ai_messages",
        sa.Column("crisis_status", sa.String(20), nullable=True, server_default="pending", comment="危机状态：pending/intervening/resolved/false_positive"),
    )
    # 处理人ID字段
    op.add_column(
        "ai_messages",
        sa.Column("crisis_resolved_by", sa.CHAR(36), sa.ForeignKey("admins.id", ondelete="SET NULL"), nullable=True, comment="处理人ID"),
    )
    # 处理备注字段
    op.add_column(
        "ai_messages",
        sa.Column("crisis_resolution_note", sa.Text, nullable=True, comment="处理备注"),
    )
    # 处理时间字段
    op.add_column(
        "ai_messages",
        sa.Column("crisis_resolved_at", sa.DateTime, nullable=True, comment="处理时间"),
    )

    # 添加索引
    op.create_index("idx_ai_messages_crisis_level", "ai_messages", ["crisis_level"])
    op.create_index("idx_ai_messages_crisis_status", "ai_messages", ["crisis_status"])


def downgrade() -> None:
    """移除危机标记和处理字段。"""
    op.drop_index("idx_ai_messages_crisis_status", "ai_messages")
    op.drop_index("idx_ai_messages_crisis_level", "ai_messages")
    op.drop_column("ai_messages", "crisis_resolved_at")
    op.drop_column("ai_messages", "crisis_resolution_note")
    op.drop_column("ai_messages", "crisis_resolved_by")
    op.drop_column("ai_messages", "crisis_status")
    op.drop_column("ai_messages", "crisis_keywords")
    op.drop_column("ai_messages", "crisis_level")
