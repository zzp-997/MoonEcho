"""节日相关模型：节日配置、用户自定义节日。"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import (
    Boolean,
    CHAR,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# holidays — 节日配置表（系统内置）
# ---------------------------------------------------------------------------

class Holiday(Base, UUIDMixin, TimestampMixin):
    """节日配置表。

    存储系统内置的节日信息，包括法定节假日、传统节日和特殊日期。
    用于定时推送任务的节日问候触发。
    """

    __tablename__ = "holidays"

    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="节日名称",
    )
    holiday_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="类型：legal/traditional/special",
    )
    month: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="月份（1-12）",
    )
    day: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="日期（1-31）",
    )
    is_lunar: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否农历",
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="节日描述",
    )
    greeting_template: Mapped[str | None] = mapped_column(
        String(200), comment="问候语模板，支持 {name} 占位符",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用",
    )

    __table_args__ = (
        Index("idx_holidays_date", "month", "day"),
        Index("idx_holidays_type", "holiday_type"),
        Index("idx_holidays_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# user_holidays — 用户自定义节日表
# ---------------------------------------------------------------------------

class UserHoliday(Base, UUIDMixin, TimestampMixin):
    """用户自定义节日表。

    用户可添加自己的重要日期，如生日、纪念日等。
    这些节日仅对该用户触发推送通知。
    """

    __tablename__ = "user_holidays"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID",
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="节日名称",
    )
    month: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="月份（1-12）",
    )
    day: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="日期（1-31）",
    )
    is_lunar: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否农历",
    )
    year: Mapped[int | None] = mapped_column(
        Integer, comment="年份（可选，用于一次性事件如面试日期）",
    )
    reminder_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否开启提醒",
    )
    reminder_time: Mapped[str | None] = mapped_column(
        String(10), default="10:00", comment="提醒时间（HH:MM 格式）",
    )
    notes: Mapped[str | None] = mapped_column(
        String(200), comment="备注信息",
    )

    # ---- 关系 ----
    user: Mapped["User"] = relationship(back_populates="user_holidays")

    __table_args__ = (
        UniqueConstraint("user_id", "month", "day", "name", name="uk_user_holidays_user_date_name"),
        Index("idx_user_holidays_user_id", "user_id"),
        Index("idx_user_holidays_date", "month", "day"),
    )


# ---------------------------------------------------------------------------
# 节日类型常量
# ---------------------------------------------------------------------------

class HolidayType:
    """节日类型常量。"""

    LEGAL = "legal"           # 法定节假日
    TRADITIONAL = "traditional"  # 传统节日
    SPECIAL = "special"       # 特殊日期（如心理健康日）
    USER = "user"             # 用户自定义


# ---------------------------------------------------------------------------
# 系统内置节日配置（用于初始化）
# ---------------------------------------------------------------------------

BUILTIN_HOLIDAYS = [
    # 法定节假日
    {"name": "元旦", "holiday_type": HolidayType.LEGAL, "month": 1, "day": 1,
     "greeting_template": "新年快乐！愿新的一年，所有美好都如约而至。"},
    {"name": "春节", "holiday_type": HolidayType.LEGAL, "month": 1, "day": 29,
     "is_lunar": True, "greeting_template": "春节快乐！愿你新的一年，万事顺遂，心想事成。"},
    {"name": "清明节", "holiday_type": HolidayType.LEGAL, "month": 4, "day": 4,
     "greeting_template": "清明时节，愿你平安顺遂，珍惜当下。"},
    {"name": "劳动节", "holiday_type": HolidayType.LEGAL, "month": 5, "day": 1,
     "greeting_template": "劳动节快乐！记得给自己放个假，好好休息一下。"},
    {"name": "端午节", "holiday_type": HolidayType.LEGAL, "month": 5, "day": 5,
     "is_lunar": True, "greeting_template": "端午安康！愿你身体健康，万事如意。"},
    {"name": "中秋节", "holiday_type": HolidayType.LEGAL, "month": 8, "day": 15,
     "is_lunar": True, "greeting_template": "中秋快乐！月圆人团圆，愿你事事圆满。"},
    {"name": "国庆节", "holiday_type": HolidayType.LEGAL, "month": 10, "day": 1,
     "greeting_template": "国庆快乐！假期愉快，好好放松一下吧。"},

    # 传统节日
    {"name": "元宵节", "holiday_type": HolidayType.TRADITIONAL, "month": 1, "day": 15,
     "is_lunar": True, "greeting_template": "元宵节快乐！愿你生活甜甜蜜蜜，团团圆圆。"},
    {"name": "七夕节", "holiday_type": HolidayType.TRADITIONAL, "month": 7, "day": 7,
     "is_lunar": True, "greeting_template": "七夕快乐！愿你被爱包围，幸福满满。"},
    {"name": "重阳节", "holiday_type": HolidayType.TRADITIONAL, "month": 9, "day": 9,
     "is_lunar": True, "greeting_template": "重阳安康！愿你健康长寿，幸福常伴。"},
    {"name": "冬至", "holiday_type": HolidayType.TRADITIONAL, "month": 12, "day": 22,
     "greeting_template": "冬至快乐！记得吃饺子/汤圆，温暖过冬。"},

    # 特殊日期
    {"name": "5·25心理健康日", "holiday_type": HolidayType.SPECIAL, "month": 5, "day": 25,
     "greeting_template": "5·25心理健康日，爱自己，从今天开始。你的情绪值得被看见。"},
    {"name": "世界睡眠日", "holiday_type": HolidayType.SPECIAL, "month": 3, "day": 21,
     "greeting_template": "世界睡眠日，愿你今晚好眠，明天精神满满。"},
    {"name": "世界精神卫生日", "holiday_type": HolidayType.SPECIAL, "month": 10, "day": 10,
     "greeting_template": "世界精神卫生日，关注心理健康，你也很重要。"},
]
