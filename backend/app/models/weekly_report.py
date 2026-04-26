"""情绪周报模型。

存储用户每周情绪周报数据，包括：
- 动态标题
- 情绪故事线
- 关键词云
- 一句看见
- 温和建议
- 下周展望
"""

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    CHAR,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class WeeklyReport(Base, UUIDMixin, TimestampMixin):
    """情绪周报表。

    存储用户每周的情绪周报，五段式结构：
    1. 动态标题 - 概括本周情绪特点
    2. 情绪故事线 - 叙事体描述情绪走势
    3. 关键词云 - 从日记中提取的高频词
    4. 一句看见 - 提炼核心感受
    5. 温和建议 - 支持性建议
    6. 下周展望 - 一句话收束
    """

    __tablename__ = "weekly_reports"

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    week_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="本周起始日期（周一）",
    )
    title: Mapped[str | None] = mapped_column(
        String(50),
        comment="动态标题，如'这周像一场漫长的周三'",
    )
    story_line: Mapped[str | None] = mapped_column(
        Text,
        comment="情绪故事线，叙事体描述本周情绪走势",
    )
    keywords: Mapped[list[str] | None] = mapped_column(
        comment="情绪关键词列表，从日记中提取3-5个高频词",
    )
    insight: Mapped[str | None] = mapped_column(
        String(100),
        comment="一句看见，提炼核心感受",
    )
    suggestion: Mapped[str | None] = mapped_column(
        String(200),
        comment="温和建议，措辞谨慎",
    )
    outlook: Mapped[str | None] = mapped_column(
        String(100),
        comment="下周展望，一句话收束",
    )
    diary_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        comment="本周分析日记数量",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="weekly_reports")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start_date", name="uk_weekly_reports_user_week"),
        Index("idx_weekly_reports_user_id", "user_id"),
        Index("idx_weekly_reports_week_start", "week_start_date"),
        Index("idx_weekly_reports_user_week", "user_id", "week_start_date"),
    )
