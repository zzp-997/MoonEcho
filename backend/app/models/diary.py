"""情绪日记相关模型：情绪日记表。"""

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    Boolean,
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

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class EmotionDiary(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """情绪日记表。

    记录用户每日情绪状态，包含情绪基调、情绪标签、内容等。
    支持离线同步，is_synced 标记是否已从客户端同步到服务端。
    唯一约束确保同一用户同一天同一客户端只有一条记录。
    """

    __tablename__ = "emotion_diaries"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    emotion_tone: Mapped[str | None] = mapped_column(
        String(30), comment="情绪基调：happy/sad/anxious/angry/calm 等",
    )
    emotion_labels: Mapped[list[str] | None] = mapped_column(
        comment="情绪标签列表（JSON），如 ['焦虑', '疲惫']",
    )
    content_text: Mapped[str | None] = mapped_column(
        Text, comment="日记内容（加密存储）",
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64), comment="内容哈希，用于完整性校验",
    )
    record_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="记录日期",
    )
    is_synced: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否已同步到服务端",
    )
    client_id: Mapped[str | None] = mapped_column(
        String(50), comment="客户端唯一标识，用于离线同步去重",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="emotion_diaries")

    __table_args__ = (
        UniqueConstraint("user_id", "record_date", "client_id", name="uk_emotion_diaries_user_date_client"),
        Index("idx_emotion_diaries_user_id", "user_id"),
        Index("idx_emotion_diaries_record_date", "record_date"),
        Index("idx_emotion_diaries_user_date", "user_id", "record_date"),
    )
