"""数据统计服务模块。

提供验证门控所需的核心指标统计服务：
1. 7日留存率统计
2. 日均 AI 对话轮次统计
3. 情绪日记 7 日连续记录率统计
4. NPS 评分收集与统计

验证门控标准：
- 7日留存率 ≥ 30% 为达标（< 15% 暂停社交层开发）
- 日均对话轮次 ≥ 10 轮为达标（< 10 回到 AI 体验优化）
- 情绪日记 7 日连续记录率 ≥ 20% 为达标（< 20% 优化日记引导）
- NPS ≥ 30 为达标（< 0 重新评估产品方向）
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diary import EmotionDiary
from app.models.nps import NPSRecord
from app.models.user import User
from app.models.user_events import UserEvent
from app.models.ai import AIMessage, AIConversation

logger = logging.getLogger(__name__)


class StatsService:
    """数据统计服务。

    提供验证门控所需的各项指标统计。
    """

    # ==================== 7日留存率统计 ====================

    async def get_retention_rate_7d(self, db: AsyncSession) -> dict[str, Any]:
        """计算 7 日留存率。

        7日留存率 = (今日活跃且注册时间在7天前的用户数) / (7天前注册的用户总数)

        验证门控：≥ 30% 为达标，< 15% 暂停社交层开发

        Returns:
            包含留存率及详细数据的字典
        """
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            seven_days_ago = today - timedelta(days=7)
            six_days_ago = today - timedelta(days=6)

            # 查询 7 天前注册的用户总数（注册时间在 7 天前当天）
            # 即 created_at >= seven_days_ago AND created_at < six_days_ago
            registered_users_stmt = select(func.count(User.id)).where(
                and_(
                    User.created_at >= seven_days_ago,
                    User.created_at < six_days_ago,
                )
            )
            result = await db.execute(registered_users_stmt)
            total_registered = result.scalar() or 0

            if total_registered == 0:
                return {
                    "retention_rate": 0.0,
                    "retained_users": 0,
                    "total_registered": 0,
                    "target": 30.0,
                    "is_met": False,
                    "status": "no_users_in_window",
                }

            # 查询这些用户在今日（过去24小时内）有活动的用户数
            # 活动定义：user_events 中有记录
            # 需要找出 7 天前注册且今日有活动的用户
            # 使用子查询方式
            active_users_stmt = select(func.count(User.id)).where(
                and_(
                    User.created_at >= seven_days_ago,
                    User.created_at < six_days_ago,
                    User.id.in_(
                        select(UserEvent.user_id).where(
                            UserEvent.created_at >= today
                        )
                    ),
                )
            )
            result = await db.execute(active_users_stmt)
            retained_users = result.scalar() or 0

            retention_rate = (retained_users / total_registered * 100) if total_registered > 0 else 0.0

            is_met = retention_rate >= 30.0
            status = "met" if is_met else "not_met"

            if retention_rate < 15.0:
                status = "critical"  # 需要暂停社交层开发

            logger.info(
                "[Stats] 7日留存率: %.2f%% (%d/%d)",
                retention_rate,
                retained_users,
                total_registered,
            )

            return {
                "retention_rate": round(retention_rate, 2),
                "retained_users": retained_users,
                "total_registered": total_registered,
                "target": 30.0,
                "is_met": is_met,
                "status": status,
            }

        except Exception as e:
            logger.error("[Stats] 计算7日留存率异常: %s", str(e))
            raise

    # ==================== 日均对话轮次统计 ====================

    async def get_daily_conversation_rounds(
        self,
        days: int = 7,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """计算用户日均 AI 对话轮次。

        统计过去 N 天内，用户与 AI 的对话轮次（每2条消息算1轮）
        日均对话轮次 = 总对话轮次 / 活跃用户数 / 天数

        验证门控：≥ 10 轮为达标，< 10 回到 AI 体验优化

        Args:
            days: 统计天数，默认为 7 天
            db: 数据库会话

        Returns:
            包含日均轮次及详细数据的字典
        """
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=days - 1)

            # 查询过去 N 天内的 AI 消息数（用户发送的消息）
            # 每2条消息算1轮
            messages_stmt = select(func.count(AIMessage.id)).where(
                and_(
                    AIMessage.role == "user",
                    AIMessage.created_at >= start_date,
                    AIMessage.created_at < today + timedelta(days=1),
                )
            )
            result = await db.execute(messages_stmt)
            total_messages = result.scalar() or 0

            # 计算轮次（用户消息数 / 2）
            total_rounds = total_messages / 2

            # 统计活跃用户数（有 AI 对话的用户）
            active_users_stmt = select(func.count(func.distinct(AIMessage.sender_id))).where(
                and_(
                    AIMessage.role == "user",
                    AIMessage.created_at >= start_date,
                    AIMessage.created_at < today + timedelta(days=1),
                )
            )
            result = await db.execute(active_users_stmt)
            active_users = result.scalar() or 0

            if active_users == 0:
                return {
                    "daily_avg_rounds": 0.0,
                    "total_rounds": 0,
                    "active_users": 0,
                    "days": days,
                    "target": 10.0,
                    "is_met": False,
                    "status": "no_active_users",
                }

            # 日均轮次 = 总轮次 / 活跃用户数 / 天数
            daily_avg_rounds = total_rounds / active_users / days

            is_met = daily_avg_rounds >= 10.0
            status = "met" if is_met else "not_met"

            logger.info(
                "[Stats] 日均对话轮次: %.2f 轮 (总轮次: %.0f, 活跃用户: %d, 天数: %d)",
                daily_avg_rounds,
                total_rounds,
                active_users,
                days,
            )

            return {
                "daily_avg_rounds": round(daily_avg_rounds, 2),
                "total_rounds": round(total_rounds, 2),
                "active_users": active_users,
                "days": days,
                "target": 10.0,
                "is_met": is_met,
                "status": status,
            }

        except Exception as e:
            logger.error("[Stats] 计算日均对话轮次异常: %s", str(e))
            raise

    # ==================== 情绪日记 7 日连续记录率 ====================

    async def get_diary_7d_continuation_rate(
        self,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """计算情绪日记 7 日连续记录率。

        7日连续记录率 = (过去7天中连续记录≥7天的用户数) / (总用户数)

        验证门控：≥ 20% 为达标，< 20% 优化日记引导

        Returns:
            包含连续记录率及详细数据的字典
        """
        try:
            today = date.today()
            week_ago = today - timedelta(days=6)  # 7天前

            # 统计过去7天每天有记录的用户
            # 先获取每个用户的记录日期集合
            diary_stmt = select(
                EmotionDiary.user_id,
                func.array_agg(EmotionDiary.record_date).label("dates"),
            ).where(
                and_(
                    EmotionDiary.record_date >= week_ago,
                    EmotionDiary.record_date <= today,
                )
            ).group_by(EmotionDiary.user_id)

            result = await db.execute(diary_stmt)
            user_diary_records = result.all()

            # 统计连续7天都有记录的用户数
            consecutive_7d_users = 0
            for row in user_diary_records:
                dates = sorted(set(row.dates))
                if len(dates) >= 7:
                    # 检查是否连续7天
                    if dates[-1] - dates[0] == timedelta(days=6):
                        consecutive_7d_users += 1

            # 获取总用户数
            total_users_stmt = select(func.count(User.id))
            result = await db.execute(total_users_stmt)
            total_users = result.scalar() or 0

            if total_users == 0:
                return {
                    "continuation_rate": 0.0,
                    "consecutive_7d_users": 0,
                    "total_users": 0,
                    "target": 20.0,
                    "is_met": False,
                    "status": "no_users",
                }

            continuation_rate = (consecutive_7d_users / total_users * 100) if total_users > 0 else 0.0

            is_met = continuation_rate >= 20.0
            status = "met" if is_met else "not_met"

            logger.info(
                "[Stats] 情绪日记7日连续记录率: %.2f%% (%d/%d)",
                continuation_rate,
                consecutive_7d_users,
                total_users,
            )

            return {
                "continuation_rate": round(continuation_rate, 2),
                "consecutive_7d_users": consecutive_7d_users,
                "total_users": total_users,
                "target": 20.0,
                "is_met": is_met,
                "status": status,
            }

        except Exception as e:
            logger.error("[Stats] 计算情绪日记7日连续记录率异常: %s", str(e))
            raise

    # ==================== NPS 收集与统计 ====================

    async def submit_nps(
        self,
        user_id: str,
        score: int,
        feedback: str | None,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """提交 NPS 评分。

        Args:
            user_id: 用户ID
            score: NPS 评分（0-10 分）
            feedback: 用户反馈（可选）
            db: 数据库会话

        Returns:
            提交结果
        """
        if not 0 <= score <= 10:
            raise ValueError("NPS 评分必须在 0-10 之间")

        try:
            nps_record = NPSRecord(
                user_id=user_id,
                score=score,
                feedback=feedback,
            )
            db.add(nps_record)
            await db.commit()

            logger.info("[Stats] 用户 %s 提交 NPS 评分: %d", user_id, score)

            return {
                "success": True,
                "message": "NPS 评分提交成功",
                "score": score,
            }

        except Exception as e:
            logger.error("[Stats] 提交NPS评分异常: %s", str(e))
            await db.rollback()
            raise

    async def get_nps_score(self, db: AsyncSession) -> dict[str, Any]:
        """获取 NPS 评分统计。

        NPS = 推荐者比例（9-10分）- 贬损者比例（0-6分）

        验证门控：≥ 30 为达标，< 0 重新评估产品方向

        Returns:
            包含 NPS 分数及详细数据的字典
        """
        try:
            # 获取所有 NPS 记录
            nps_stmt = select(NPSRecord)
            result = await db.execute(nps_stmt)
            nps_records = result.scalars().all()

            if not nps_records:
                return {
                    "nps_score": 0,
                    "total_responses": 0,
                    "promoters": 0,
                    "passives": 0,
                    "detractors": 0,
                    "target": 30,
                    "is_met": False,
                    "status": "no_data",
                }

            total = len(nps_records)
            promoters = sum(1 for r in nps_records if r.score >= 9)  # 9-10 分
            passives = sum(1 for r in nps_records if 7 <= r.score <= 8)  # 7-8 分
            detractors = sum(1 for r in nps_records if r.score <= 6)  # 0-6 分

            promoter_pct = (promoters / total * 100) if total > 0 else 0
            detractor_pct = (detractors / total * 100) if total > 0 else 0

            nps_score = int(promoter_pct - detractor_pct)

            is_met = nps_score >= 30
            status = "met" if is_met else "not_met"

            if nps_score < 0:
                status = "critical"  # 需要重新评估产品方向

            logger.info(
                "[Stats] NPS 评分: %d (推荐者: %d, 中立: %d, 贬损者: %d, 总数: %d)",
                nps_score,
                promoters,
                passives,
                detractors,
                total,
            )

            return {
                "nps_score": nps_score,
                "total_responses": total,
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
                "target": 30,
                "is_met": is_met,
                "status": status,
            }

        except Exception as e:
            logger.error("[Stats] 计算NPS评分异常: %s", str(e))
            raise

    # ==================== 综合验证门控状态 ====================

    async def get_verification_gate_status(
        self,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """获取验证门控综合状态。

        Returns:
            包含所有指标状态的字典
        """
        try:
            # 并行获取所有指标
            retention = await self.get_retention_rate_7d(db)
            conversation = await self.get_daily_conversation_rounds(db=db)
            diary = await self.get_diary_7d_continuation_rate(db)
            nps = await self.get_nps_score(db)

            # 计算综合状态
            all_met = all([
                retention["is_met"],
                conversation["is_met"],
                diary["is_met"],
                nps["is_met"],
            ])

            return {
                "overall_status": "passed" if all_met else "pending",
                "metrics": {
                    "retention_rate_7d": retention,
                    "daily_conversation_rounds": conversation,
                    "diary_7d_continuation": diary,
                    "nps_score": nps,
                },
            }

        except Exception as e:
            logger.error("[Stats] 获取验证门控状态异常: %s", str(e))
            raise


def create_stats_service() -> StatsService:
    """创建统计服务的工厂函数。"""
    return StatsService()


# ==================== 用户事件记录 ====================

async def record_user_event(
    user_id: str | None,
    event_type: str,
    event_data: dict[str, Any] | None,
    source: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """记录用户行为事件。

    Args:
        user_id: 用户ID（可选，未登录时为None）
        event_type: 事件类型
        event_data: 事件附加数据
        source: 事件来源（app/web/mini_program）
        db: 数据库会话

    Returns:
        记录结果
    """
    try:
        # 如果没有 user_id，跳过记录（仅记录已登录用户的事件）
        if not user_id:
            return {
                "success": True,
                "message": "未登录用户事件跳过记录",
                "recorded": False,
            }

        event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            source=source,
        )
        db.add(event)
        await db.commit()

        logger.info(
            "[Stats] 记录用户事件: user_id=%s, event_type=%s",
            user_id,
            event_type,
        )

        return {
            "success": True,
            "message": "事件记录成功",
            "recorded": True,
        }

    except Exception as e:
        logger.error("[Stats] 记录用户事件异常: %s", str(e))
        await db.rollback()
        # 不抛出异常，避免影响前端业务逻辑
        return {
            "success": True,
            "message": "事件记录失败（静默处理）",
            "recorded": False,
            "error": str(e),
        }


async def batch_record_events(
    events: list[dict[str, Any]],
    db: AsyncSession,
) -> dict[str, Any]:
    """批量记录用户行为事件。

    Args:
        events: 事件列表，每项包含 user_id, event_type, event_data, source
        db: 数据库会话

    Returns:
        批量记录结果
    """
    recorded_count = 0
    skipped_count = 0

    try:
        for event_data in events:
            user_id = event_data.get("user_id")
            event_type = event_data.get("event_type")
            event_info = event_data.get("event_data")
            source = event_data.get("source", "app")

            # 跳过无效事件
            if not user_id or not event_type:
                skipped_count += 1
                continue

            event = UserEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_info,
                source=source,
            )
            db.add(event)
            recorded_count += 1

        await db.commit()

        logger.info(
            "[Stats] 批量记录用户事件: 成功=%d, 跳过=%d",
            recorded_count,
            skipped_count,
        )

        return {
            "message": f"批量记录完成，成功: {recorded_count}, 跳过: {skipped_count}",
            "recorded_count": recorded_count,
            "skipped_count": skipped_count,
        }

    except Exception as e:
        logger.error("[Stats] 批量记录用户事件异常: %s", str(e))
        await db.rollback()
        return {
            "message": "批量记录失败（静默处理）",
            "recorded_count": 0,
            "skipped_count": len(events),
            "error": str(e),
        }
