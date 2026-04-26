"""节日系统表结构

Revision ID: 0005_holidays
Revises: 0004_notification_settings
Create Date: 2026-04-26

创建节日相关表：
- holidays: 系统内置节日配置表
- user_holidays: 用户自定义节日表

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_holidays"
down_revision: Union[str, None] = "0004_notification_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建节日相关表结构。"""

    # ----------------------------------------------------------
    # holidays — 节日配置表（系统内置）
    # ----------------------------------------------------------
    op.create_table(
        "holidays",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("name", sa.String(50), nullable=False, comment="节日名称"),
        sa.Column("holiday_type", sa.String(20), nullable=False, comment="类型：legal/traditional/special"),
        sa.Column("month", sa.Integer, nullable=False, comment="月份（1-12）"),
        sa.Column("day", sa.Integer, nullable=False, comment="日期（1-31）"),
        sa.Column("is_lunar", sa.Boolean, default=False, server_default="0", comment="是否农历"),
        sa.Column("description", sa.Text, comment="节日描述"),
        sa.Column("greeting_template", sa.String(200), comment="问候语模板"),
        sa.Column("is_active", sa.Boolean, default=True, server_default="1", comment="是否启用"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_holidays_date", "holidays", ["month", "day"])
    op.create_index("idx_holidays_type", "holidays", ["holiday_type"])
    op.create_index("idx_holidays_active", "holidays", ["is_active"])

    # ----------------------------------------------------------
    # user_holidays — 用户自定义节日表
    # ----------------------------------------------------------
    op.create_table(
        "user_holidays",
        sa.Column("id", sa.CHAR(36), primary_key=True, comment="主键UUID"),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("name", sa.String(50), nullable=False, comment="节日名称"),
        sa.Column("month", sa.Integer, nullable=False, comment="月份（1-12）"),
        sa.Column("day", sa.Integer, nullable=False, comment="日期（1-31）"),
        sa.Column("is_lunar", sa.Boolean, default=False, server_default="0", comment="是否农历"),
        sa.Column("year", sa.Integer, comment="年份（可选，用于一次性事件）"),
        sa.Column("reminder_enabled", sa.Boolean, default=True, server_default="1", comment="是否开启提醒"),
        sa.Column("reminder_time", sa.String(10), default="10:00", comment="提醒时间（HH:MM 格式）"),
        sa.Column("notes", sa.String(200), comment="备注信息"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "month", "day", "name", name="uk_user_holidays_user_date_name"),
    )
    op.create_index("idx_user_holidays_user_id", "user_holidays", ["user_id"])
    op.create_index("idx_user_holidays_date", "user_holidays", ["month", "day"])

    # ----------------------------------------------------------
    # 插入系统内置节日数据
    # ----------------------------------------------------------
    # 注意：农历节日的公历日期每年变化，这些日期仅供参考，
    # 实际运行时需要通过农历转换算法或定期更新

    # 使用固定的 UUID，确保迁移的可重复性
    holidays_data = [
        # 法定节假日
        {"id": "h10000001-0000-0000-0000-000000000001", "name": "元旦", "holiday_type": "legal", "month": 1, "day": 1,
         "greeting_template": "新年快乐！愿新的一年，所有美好都如约而至。"},
        {"id": "h10000001-0000-0000-0000-000000000002", "name": "春节", "holiday_type": "legal", "month": 1, "day": 29,
         "is_lunar": True, "greeting_template": "春节快乐！愿你新的一年，万事顺遂，心想事成。"},
        {"id": "h10000001-0000-0000-0000-000000000003", "name": "清明节", "holiday_type": "legal", "month": 4, "day": 4,
         "greeting_template": "清明时节，愿你平安顺遂，珍惜当下。"},
        {"id": "h10000001-0000-0000-0000-000000000004", "name": "劳动节", "holiday_type": "legal", "month": 5, "day": 1,
         "greeting_template": "劳动节快乐！记得给自己放个假，好好休息一下。"},
        {"id": "h10000001-0000-0000-0000-000000000005", "name": "端午节", "holiday_type": "legal", "month": 5, "day": 5,
         "is_lunar": True, "greeting_template": "端午安康！愿你身体健康，万事如意。"},
        {"id": "h10000001-0000-0000-0000-000000000006", "name": "中秋节", "holiday_type": "legal", "month": 8, "day": 15,
         "is_lunar": True, "greeting_template": "中秋快乐！月圆人团圆，愿你事事圆满。"},
        {"id": "h10000001-0000-0000-0000-000000000007", "name": "国庆节", "holiday_type": "legal", "month": 10, "day": 1,
         "greeting_template": "国庆快乐！假期愉快，好好放松一下吧。"},

        # 传统节日
        {"id": "h10000002-0000-0000-0000-000000000001", "name": "元宵节", "holiday_type": "traditional", "month": 1, "day": 15,
         "is_lunar": True, "greeting_template": "元宵节快乐！愿你生活甜甜蜜蜜，团团圆圆。"},
        {"id": "h10000002-0000-0000-0000-000000000002", "name": "七夕节", "holiday_type": "traditional", "month": 7, "day": 7,
         "is_lunar": True, "greeting_template": "七夕快乐！愿你被爱包围，幸福满满。"},
        {"id": "h10000002-0000-0000-0000-000000000003", "name": "重阳节", "holiday_type": "traditional", "month": 9, "day": 9,
         "is_lunar": True, "greeting_template": "重阳安康！愿你健康长寿，幸福常伴。"},
        {"id": "h10000002-0000-0000-0000-000000000004", "name": "冬至", "holiday_type": "traditional", "month": 12, "day": 22,
         "greeting_template": "冬至快乐！记得吃饺子/汤圆，温暖过冬。"},

        # 特殊日期
        {"id": "h10000003-0000-0000-0000-000000000001", "name": "5·25心理健康日", "holiday_type": "special", "month": 5, "day": 25,
         "greeting_template": "5·25心理健康日，爱自己，从今天开始。你的情绪值得被看见。"},
        {"id": "h10000003-0000-0000-0000-000000000002", "name": "世界睡眠日", "holiday_type": "special", "month": 3, "day": 21,
         "greeting_template": "世界睡眠日，愿你今晚好眠，明天精神满满。"},
        {"id": "h10000003-0000-0000-0000-000000000003", "name": "世界精神卫生日", "holiday_type": "special", "month": 10, "day": 10,
         "greeting_template": "世界精神卫生日，关注心理健康，你也很重要。"},
    ]

    # 批量插入
    op.bulk_insert(
        sa.table(
            "holidays",
            sa.column("id", sa.String),
            sa.column("name", sa.String),
            sa.column("holiday_type", sa.String),
            sa.column("month", sa.Integer),
            sa.column("day", sa.Integer),
            sa.column("is_lunar", sa.Boolean),
            sa.column("greeting_template", sa.String),
        ),
        holidays_data,
    )


def downgrade() -> None:
    """删除节日相关表结构。"""
    op.drop_table("user_holidays")
    op.drop_table("holidays")
