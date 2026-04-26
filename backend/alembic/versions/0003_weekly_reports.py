"""添加情绪周报表

Revision ID: 0003_weekly_reports
Revises: 0002_ai_message_crisis_fields
Create Date: 2026-04-26

创建情绪周报表，存储用户每周情绪周报数据。

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_weekly_reports"
down_revision: Union[str, None] = "0002_ai_message_crisis_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建情绪周报表。"""
    # ----------------------------------------------------------
    # weekly_reports — 情绪周报表
    # ----------------------------------------------------------
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column(
            "user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="用户ID",
        ),
        sa.Column(
            "week_start_date",
            sa.Date,
            nullable=False,
            comment="本周起始日期（周一）",
        ),
        sa.Column(
            "title",
            sa.String(50),
            comment="动态标题，如'这周像一场漫长的周三'",
        ),
        sa.Column(
            "story_line",
            sa.Text,
            comment="情绪故事线，叙事体描述本周情绪走势",
        ),
        sa.Column(
            "keywords",
            sa.JSON,
            comment="情绪关键词列表，从日记中提取3-5个高频词",
        ),
        sa.Column(
            "insight",
            sa.String(100),
            comment="一句看见，提炼核心感受",
        ),
        sa.Column(
            "suggestion",
            sa.String(200),
            comment="温和建议，措辞谨慎",
        ),
        sa.Column(
            "outlook",
            sa.String(100),
            comment="下周展望，一句话收束",
        ),
        sa.Column(
            "diary_count",
            sa.Integer,
            default=0,
            server_default="0",
            comment="本周分析日记数量",
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
        sa.UniqueConstraint("user_id", "week_start_date", name="uk_weekly_reports_user_week"),
    )
    op.create_index("idx_weekly_reports_user_id", "weekly_reports", ["user_id"])
    op.create_index("idx_weekly_reports_week_start", "weekly_reports", ["week_start_date"])
    op.create_index("idx_weekly_reports_user_week", "weekly_reports", ["user_id", "week_start_date"])


def downgrade() -> None:
    """删除情绪周报表。"""
    op.drop_index("idx_weekly_reports_user_week", table_name="weekly_reports")
    op.drop_index("idx_weekly_reports_week_start", table_name="weekly_reports")
    op.drop_index("idx_weekly_reports_user_id", table_name="weekly_reports")
    op.drop_table("weekly_reports")
