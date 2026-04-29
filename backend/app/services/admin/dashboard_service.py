"""数据看板服务模块。

提供管理后台数据看板的统计数据能力：
- 概览数据（DAU、新增用户、AI对话次数等）
- 用户增长趋势（按日/周/月）
- 留存数据（次日/7日/30日留存）
- 情绪分布统计
- AI 服务数据

注意：开发阶段返回 Mock 数据，实现框架预留，方便后续接入真实数据。
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, Conversation, Friendship
from app.models.diary import EmotionDiary
from app.models.user import User
from app.schemas.admin_dashboard import (
    AIServiceDataItem,
    AIServiceDataResponse,
    DashboardOverviewResponse,
    DashboardPeriodRequest,
    EmotionDistributionItem,
    EmotionDistributionResponse,
    RetentionDataItem,
    RetentionResponse,
    UserGrowthTrendItem,
    UserGrowthTrendResponse,
)
from app.schemas.base import PaginatedResponse

logger = logging.getLogger(__name__)


class DashboardService:
    """数据看板服务。

    依赖外部注入：
    - redis: Redis 客户端（用于缓存统计数据）
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # ---------------------------------------------------------------------------
    # 概览数据
    # ---------------------------------------------------------------------------

    async def get_overview(
        self,
        db: AsyncSession,
    ) -> DashboardOverviewResponse:
        """获取数据看板概览数据。

        Args:
            db: 数据库会话

        Returns:
            DashboardOverviewResponse: 概览数据
        """
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # 总用户数
        total_users_result = await db.execute(
            select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
        )
        total_users = total_users_result.scalar() or 0

        # DAU（今日活跃用户）
        dau_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.is_active == True,  # noqa: E712
                User.last_active_at >= today_start,
            )
        )
        dau = dau_result.scalar() or 0

        # WAU（周活跃用户）
        wau_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.is_active == True,  # noqa: E712
                User.last_active_at >= week_start,
            )
        )
        wau = wau_result.scalar() or 0

        # MAU（月活跃用户）
        mau_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.is_active == True,  # noqa: E712
                User.last_active_at >= month_start,
            )
        )
        mau = mau_result.scalar() or 0

        # 今日新增用户
        new_users_today_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= today_start,
            )
        )
        new_users_today = new_users_today_result.scalar() or 0

        # 本周新增用户
        new_users_week_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= week_start,
            )
        )
        new_users_week = new_users_week_result.scalar() or 0

        # 本月新增用户
        new_users_month_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= month_start,
            )
        )
        new_users_month = new_users_month_result.scalar() or 0

        # 今日日记数
        diaries_today_result = await db.execute(
            select(func.count()).select_from(EmotionDiary).where(
                EmotionDiary.created_at >= today_start,
                EmotionDiary.is_active == True,  # noqa: E712
            )
        )
        diaries_today = diaries_today_result.scalar() or 0

        # 今日私聊消息数
        private_messages_today_result = await db.execute(
            select(func.count()).select_from(ChatMessage).where(
                ChatMessage.created_at >= today_start,
            )
        )
        private_messages_today = private_messages_today_result.scalar() or 0

        # 今日新增好友关系
        new_friendships_today_result = await db.execute(
            select(func.count()).select_from(Friendship).where(
                Friendship.created_at >= today_start,
            )
        )
        new_friendships_today = new_friendships_today_result.scalar() or 0

        # AI 对话数据（目前使用 mock 数据，后续可接入 AI 对话记录）
        # TODO: 接入 AIConversation 表统计
        ai_conversations_today = 0
        ai_conversations_week = 0
        ai_conversations_month = 0
        avg_ai_turns = 0.0

        # 树洞帖子数（使用 posts 表中的树洞类型）
        # TODO: 接入 TreeholePost 表统计
        treehole_posts_today = 0

        # 动态数
        # TODO: 接入 Post 表统计
        posts_today = 0

        # 待处理举报数
        # TODO: 接入 Report 表统计
        pending_reports = 0

        # 今日危机事件数
        # TODO: 接入危机事件表统计
        crisis_events_today = 0

        return DashboardOverviewResponse(
            total_users=total_users,
            dau=dau,
            wau=wau,
            mau=mau,
            new_users_today=new_users_today,
            new_users_week=new_users_week,
            new_users_month=new_users_month,
            ai_conversations_today=ai_conversations_today,
            ai_conversations_week=ai_conversations_week,
            ai_conversations_month=ai_conversations_month,
            avg_ai_turns=avg_ai_turns,
            new_friendships_today=new_friendships_today,
            private_messages_today=private_messages_today,
            diaries_today=diaries_today,
            treehole_posts_today=treehole_posts_today,
            posts_today=posts_today,
            pending_reports=pending_reports,
            crisis_events_today=crisis_events_today,
        )

    # ---------------------------------------------------------------------------
    # 用户增长趋势
    # ---------------------------------------------------------------------------

    async def get_user_growth_trend(
        self,
        db: AsyncSession,
        params: DashboardPeriodRequest,
    ) -> UserGrowthTrendResponse:
        """获取用户增长趋势数据。

        Args:
            db: 数据库会话
            params: 请求参数

        Returns:
            UserGrowthTrendResponse: 用户增长趋势
        """
        now = datetime.now(timezone.utc)
        end_date = params.end_date or now.date()
        period = params.period

        # 根据周期计算天数
        if period == "day":
            days = 30  # 显示最近30天
        elif period == "week":
            days = 90  # 显示最近12周
        else:  # month
            days = 365  # 显示最近12个月

        start_date = params.start_date or (end_date - timedelta(days=days))

        # 查询每日新增用户
        # 使用 PostgreSQL 的 date_trunc 函数按日期分组
        data = []
        current_date = start_date
        cumulative_users = 0

        # 先获取起始日期之前的总用户数
        start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        base_count_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at < start_datetime,
            )
        )
        cumulative_users = base_count_result.scalar() or 0

        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)

            # 新增用户数
            new_users_result = await db.execute(
                select(func.count()).select_from(User).where(
                    User.created_at >= day_start,
                    User.created_at < day_end,
                )
            )
            new_users = new_users_result.scalar() or 0

            # 活跃用户数
            active_users_result = await db.execute(
                select(func.count()).select_from(User).where(
                    User.is_active == True,  # noqa: E712
                    User.last_active_at >= day_start,
                    User.last_active_at < day_end,
                )
            )
            active_users = active_users_result.scalar() or 0

            cumulative_users += new_users

            data.append(UserGrowthTrendItem(
                stat_date=current_date,
                new_users=new_users,
                total_users=cumulative_users,
                active_users=active_users,
            ))

            current_date += timedelta(days=1)

        return UserGrowthTrendResponse(
            period=period,
            data=data,
        )

    # ---------------------------------------------------------------------------
    # 留存数据
    # ---------------------------------------------------------------------------

    async def get_retention(
        self,
        db: AsyncSession,
        params: DashboardPeriodRequest,
    ) -> RetentionResponse:
        """获取留存数据。

        Args:
            db: 数据库会话
            params: 请求参数

        Returns:
            RetentionResponse: 留存数据

        Note:
            开发阶段返回 Mock 数据，后续接入真实计算。
        """
        now = datetime.now(timezone.utc)
        end_date = params.end_date or now.date()
        period = params.period

        if period == "day":
            days = 30  # 分析最近30天的注册用户
        else:  # week
            days = 90  # 分析最近90天的注册用户

        start_date = params.start_date or (end_date - timedelta(days=days))

        # Mock 留存数据
        # TODO: 实现真实的留存计算
        data = []
        current_date = start_date

        while current_date <= end_date:
            # 模拟留存数据
            data.append(RetentionDataItem(
                cohort_date=current_date,
                total_users=100,  # Mock
                day_1_retention=45.5,  # Mock
                day_7_retention=25.3,  # Mock
                day_30_retention=12.8,  # Mock
            ))
            current_date += timedelta(days=1)

        return RetentionResponse(
            period=period,
            avg_day_1_retention=45.2,
            avg_day_7_retention=25.1,
            avg_day_30_retention=12.5,
            data=data[:30],  # 只返回最近30天的数据
        )

    # ---------------------------------------------------------------------------
    # 情绪分布统计
    # ---------------------------------------------------------------------------

    async def get_emotion_distribution(
        self,
        db: AsyncSession,
        params: DashboardPeriodRequest,
    ) -> EmotionDistributionResponse:
        """获取情绪分布统计。

        Args:
            db: 数据库会话
            params: 请求参数

        Returns:
            EmotionDistributionResponse: 情绪分布
        """
        now = datetime.now(timezone.utc)
        end_date = params.end_date or now.date()
        period = params.period

        # 根据周期计算起始日期
        if period == "day":
            start_date = end_date
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        else:  # month
            start_date = end_date - timedelta(days=30)

        start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)

        # 查询情绪分布
        result = await db.execute(
            select(
                EmotionDiary.emotion_tone,
                func.count().label("count"),
            ).where(
                EmotionDiary.created_at >= start_datetime,
                EmotionDiary.created_at < end_datetime,
                EmotionDiary.emotion_tone.isnot(None),
                EmotionDiary.is_active == True,  # noqa: E712
            ).group_by(EmotionDiary.emotion_tone)
        )
        rows = result.all()

        # 计算总数
        total = sum(row.count for row in rows)

        # 构建分布数据
        distribution = []
        emotion_names = {
            "happy": "开心",
            "sad": "难过",
            "anxious": "焦虑",
            "angry": "愤怒",
            "calm": "平静",
            "excited": "兴奋",
            "tired": "疲惫",
            "hopeful": "充满希望",
        }

        for row in rows:
            emotion_tone = row.emotion_tone
            count = row.count
            percentage = (count / total * 100) if total > 0 else 0

            distribution.append(EmotionDistributionItem(
                emotion_tone=emotion_names.get(emotion_tone, emotion_tone),
                count=count,
                percentage=round(percentage, 2),
            ))

        # 按数量降序排序
        distribution.sort(key=lambda x: x.count, reverse=True)

        return EmotionDistributionResponse(
            period=period,
            total_diaries=total,
            distribution=distribution,
        )

    # ---------------------------------------------------------------------------
    # AI 服务数据
    # ---------------------------------------------------------------------------

    async def get_ai_service_data(
        self,
        db: AsyncSession,
        params: DashboardPeriodRequest,
    ) -> AIServiceDataResponse:
        """获取 AI 服务数据。

        Args:
            db: 数据库会话
            params: 请求参数

        Returns:
            AIServiceDataResponse: AI 服务数据

        Note:
            开发阶段返回 Mock 数据，后续接入 AIConversation 表。
        """
        now = datetime.now(timezone.utc)
        end_date = params.end_date or now.date()
        period = params.period

        # 根据周期计算天数
        if period == "day":
            days = 30
        elif period == "week":
            days = 90
        else:
            days = 365

        start_date = params.start_date or (end_date - timedelta(days=days))

        # Mock AI 服务数据
        # TODO: 接入 AIConversation 表统计
        data = []
        current_date = start_date

        while current_date <= end_date:
            data.append(AIServiceDataItem(
                stat_date=current_date,
                conversations=150,  # Mock
                avg_turns=5.2,  # Mock
                avg_duration_seconds=120.5,  # Mock
            ))
            current_date += timedelta(days=1)

        return AIServiceDataResponse(
            period=period,
            total_conversations=len(data) * 150,  # Mock
            total_users=500,  # Mock
            overall_avg_turns=5.5,
            data=data[:30],  # 只返回最近30天的数据
        )
