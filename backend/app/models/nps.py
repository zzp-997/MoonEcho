"""NPS 评分记录表。

用于收集内测用户的 NPS（Net Promoter Score）评分，
作为验证门控的关键指标之一。
"""

from __future__ import annotations

from sqlalchemy import CHAR, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class NPSRecord(Base, UUIDMixin, TimestampMixin):
    """NPS 评分记录表。

    存储用户对产品的 NPS 评分（0-10分）。
    NPS = 推荐者比例（9-10分）- 贬损者比例（0-6分）
    目标：≥ 30 分为达标
    """

    __tablename__ = "nps_records"

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="NPS 评分（0-10 分）",
    )
    feedback: Mapped[str | None] = mapped_column(
        comment="用户反馈（可选）",
    )

    __table_args__ = (
        Index("idx_nps_records_user_id", "user_id"),
        Index("idx_nps_records_created_at", "created_at"),
    )
