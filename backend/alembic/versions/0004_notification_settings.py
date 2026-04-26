"""添加通知设置字段和通知类型索引

Revision ID: 0004_notification_settings
Revises: 0003_weekly_reports
Create Date: 2026-04-26

更新通知表和推送记录表，添加通知设置字段。

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_notification_settings"
down_revision: Union[str, None] = "0003_weekly_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加通知相关字段和索引。"""
    # ----------------------------------------------------------
    # notifications 表 — 添加 payload 字段索引
    # ----------------------------------------------------------
    # payload 字段已在原表中定义为 JSON，无需添加
    # 这里添加复合索引优化查询性能
    op.create_index(
        "idx_notifications_user_type",
        "notifications",
        ["user_id", "type"],
    )
    op.create_index(
        "idx_notifications_user_unread",
        "notifications",
        ["user_id", "is_read"],
    )

    # ----------------------------------------------------------
    # push_records 表 — 添加 sent_at 索引
    # ----------------------------------------------------------
    op.create_index(
        "idx_push_records_sent_at",
        "push_records",
        ["sent_at"],
    )
    op.create_index(
        "idx_push_records_user_type",
        "push_records",
        ["user_id", "push_type"],
    )


def downgrade() -> None:
    """删除通知相关索引。"""
    op.drop_index("idx_push_records_user_type", table_name="push_records")
    op.drop_index("idx_push_records_sent_at", table_name="push_records")
    op.drop_index("idx_notifications_user_unread", table_name="notifications")
    op.drop_index("idx_notifications_user_type", table_name="notifications")