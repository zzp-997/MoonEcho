"""举报相关模型：举报记录表。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Report(Base, UUIDMixin, TimestampMixin):
    """举报记录表。

    用户举报内容或他人时创建，管理员审核处理。
    支持申诉流程，记录完整处理链路。
    """

    __tablename__ = "reports"

    reporter_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="举报人ID",
    )
    reported_user_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="SET NULL"), comment="被举报人ID",
    )
    reported_content_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="举报内容类型：post/treehole_post/comment/user",
    )
    reported_content_id: Mapped[str | None] = mapped_column(
        CHAR(36), comment="举报内容ID",
    )
    report_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="举报分类：porn/ad/harassment/abuse/scam/self_harm/other",
    )
    reason: Mapped[str | None] = mapped_column(
        Text, comment="详细原因",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending",
        comment="状态：pending/processing/approved/rejected",
    )
    process_result: Mapped[str | None] = mapped_column(
        Text, comment="处理结果说明",
    )
    processed_by: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("admins.id", ondelete="SET NULL"), comment="处理人管理员ID",
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="处理时间",
    )
    appeal_status: Mapped[str | None] = mapped_column(
        String(20), comment="申诉状态：pending/approved/rejected",
    )
    appeal_reason: Mapped[str | None] = mapped_column(
        Text, comment="申诉理由",
    )

    __table_args__ = (
        Index("idx_reports_reporter_id", "reporter_id"),
        Index("idx_reports_reported_user_id", "reported_user_id"),
        Index("idx_reports_content", "reported_content_type", "reported_content_id"),
        Index("idx_reports_status", "status"),
        Index("idx_reports_type", "report_type"),
        Index("idx_reports_created", "created_at"),
    )
