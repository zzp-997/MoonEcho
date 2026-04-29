"""数据看板相关请求/响应模型。

包含概览数据、用户增长趋势、留存数据、情绪分布、AI 服务数据等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 概览数据
# ---------------------------------------------------------------------------

class DashboardOverviewResponse(BaseSchema):
    """数据看板概览响应模型。"""

    # 用户数据
    total_users: int = Field(..., description="总用户数")
    dau: int = Field(..., description="日活跃用户数（DAU）")
    wau: int = Field(..., description="周活跃用户数（WAU）")
    mau: int = Field(..., description="月活跃用户数（MAU）")
    new_users_today: int = Field(..., description="今日新增用户")
    new_users_week: int = Field(..., description="本周新增用户")
    new_users_month: int = Field(..., description="本月新增用户")

    # AI 服务数据
    ai_conversations_today: int = Field(..., description="今日 AI 对话次数")
    ai_conversations_week: int = Field(..., description="本周 AI 对话次数")
    ai_conversations_month: int = Field(..., description="本月 AI 对话次数")
    avg_ai_turns: float = Field(..., description="AI 对话平均轮次")

    # 社交数据
    new_friendships_today: int = Field(..., description="今日新增好友关系")
    private_messages_today: int = Field(..., description="今日私聊消息数")

    # 内容数据
    diaries_today: int = Field(..., description="今日日记数")
    treehole_posts_today: int = Field(..., description="今日树洞帖子数")
    posts_today: int = Field(..., description="今日动态数")

    # 举报数据
    pending_reports: int = Field(..., description="待处理举报数")
    crisis_events_today: int = Field(..., description="今日危机事件数")


# ---------------------------------------------------------------------------
# 用户增长趋势
# ---------------------------------------------------------------------------

class UserGrowthTrendItem(BaseSchema):
    """用户增长趋势单项。"""

    stat_date: date = Field(..., description="日期")
    new_users: int = Field(..., description="新增用户数")
    total_users: int = Field(..., description="累计用户数")
    active_users: int = Field(..., description="活跃用户数")


class UserGrowthTrendResponse(BaseSchema):
    """用户增长趋势响应模型。"""

    period: str = Field(..., description="统计周期：day/week/month")
    data: list[UserGrowthTrendItem] = Field(default_factory=list, description="趋势数据")


# ---------------------------------------------------------------------------
# 留存数据
# ---------------------------------------------------------------------------

class RetentionDataItem(BaseSchema):
    """留存数据单项。"""

    cohort_date: date = Field(..., description="注册日期（同期群）")
    total_users: int = Field(..., description="该日注册用户数")
    day_1_retention: float | None = Field(None, description="次日留存率（%）")
    day_7_retention: float | None = Field(None, description="7日留存率（%）")
    day_30_retention: float | None = Field(None, description="30日留存率（%）")


class RetentionResponse(BaseSchema):
    """留存数据响应模型。"""

    period: str = Field(..., description="统计周期：day/week")
    avg_day_1_retention: float = Field(..., description="平均次日留存率（%）")
    avg_day_7_retention: float = Field(..., description="平均7日留存率（%）")
    avg_day_30_retention: float = Field(..., description="平均30日留存率（%）")
    data: list[RetentionDataItem] = Field(default_factory=list, description="留存详情")


# ---------------------------------------------------------------------------
# 情绪分布统计
# ---------------------------------------------------------------------------

class EmotionDistributionItem(BaseSchema):
    """情绪分布单项。"""

    emotion_tone: str = Field(..., description="情绪基调：happy/sad/anxious/angry/calm 等")
    count: int = Field(..., description="日记数量")
    percentage: float = Field(..., description="占比（%）")


class EmotionDistributionResponse(BaseSchema):
    """情绪分布响应模型。"""

    period: str = Field(..., description="统计周期：day/week/month")
    total_diaries: int = Field(..., description="日记总数")
    distribution: list[EmotionDistributionItem] = Field(default_factory=list, description="分布详情")


# ---------------------------------------------------------------------------
# AI 服务数据
# ---------------------------------------------------------------------------

class AIServiceDataItem(BaseSchema):
    """AI 服务数据单项。"""

    stat_date: date = Field(..., description="日期")
    conversations: int = Field(..., description="对话次数")
    avg_turns: float = Field(..., description="平均轮次")
    avg_duration_seconds: float | None = Field(None, description="平均对话时长（秒）")


class AIServiceDataResponse(BaseSchema):
    """AI 服务数据响应模型。"""

    period: str = Field(..., description="统计周期：day/week/month")
    total_conversations: int = Field(..., description="对话总次数")
    total_users: int = Field(..., description="使用 AI 的用户数")
    overall_avg_turns: float = Field(..., description="总体平均轮次")
    data: list[AIServiceDataItem] = Field(default_factory=list, description="趋势数据")


# ---------------------------------------------------------------------------
# 查询参数
# ---------------------------------------------------------------------------

class DashboardPeriodRequest(BaseSchema):
    """数据看板时间范围请求参数。"""

    period: str = Field(
        default="day",
        description="统计周期：day（日）/week（周）/month（月）",
    )
    start_date: date | None = Field(None, description="开始日期（可选，默认自动计算）")
    end_date: date | None = Field(None, description="结束日期（可选，默认今天）")

    def get_period_days(self) -> int:
        """根据 period 获取天数。"""
        return {
            "day": 1,
            "week": 7,
            "month": 30,
        }.get(self.period, 1)
