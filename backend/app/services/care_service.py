"""AI 关怀推送服务模块。

核心业务逻辑层，封装以下能力：
- 晚安问候推送
- 早安问候推送
- 情绪低谷关怀推送
- 节日问候推送
- 重要事件跟进推送
- 推送频率控制（Redis 缓存）
- AI 生成个性化推送文案
"""

from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings
from app.models.ai import AIMemory
from app.models.diary import EmotionDiary
from app.models.holiday import Holiday, UserHoliday
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationType
from app.services.ai_chat import GLMChatService, create_ai_chat_service
from app.services.notification_service import NotificationService
from app.services.push import PushProtocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

REDIS_KEY_CARE_FREQUENCY = "care:freq:{user_id}:{care_type}:{period}"
REDIS_KEY_CARE_SENT_TODAY = "care:sent:{user_id}:{care_type}:{date}"


# ---------------------------------------------------------------------------
# 关怀类型常量
# ---------------------------------------------------------------------------

class CareType:
    """关怀推送类型常量。"""

    GOOD_NIGHT = "good_night"      # 晚安问候
    GOOD_MORNING = "good_morning"   # 早安问候
    LOW_MOOD = "low_mood"          # 情绪低谷关怀
    HOLIDAY = "holiday"            # 节日问候
    EVENT_FOLLOW = "event_follow"  # 重要事件跟进


# ---------------------------------------------------------------------------
# 频率限制配置
# ---------------------------------------------------------------------------

CARE_FREQUENCY_LIMITS = {
    CareType.GOOD_NIGHT: {"max_count": 3, "period": "week"},
    CareType.GOOD_MORNING: {"max_count": 2, "period": "week"},
    CareType.LOW_MOOD: {"max_count": 2, "period": "month"},
    CareType.HOLIDAY: {"max_count": 1, "period": "day"},
    CareType.EVENT_FOLLOW: {"max_count": 1, "period": "day"},
}


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

CARE_PROMPT_TEMPLATE = """你是一个温暖的 AI 陪伴助手，正在为用户生成一条简短的关怀推送文案。

## 用户信息
- 昵称：{nickname}
- 最近情绪状态：{recent_mood}

## 推送类型
{care_type_desc}

## 输出要求
1. 文案长度控制在 30 字以内
2. 语气温和、不评判、不说教
3. 不要使用感叹号，避免过度热情
4. 不要使用"你应该""你需要"等命令式语言
5. 如果有上下文信息，可以适当提及，但不要生硬
6. 输出纯文本，不要包含任何 Markdown 格式

## 示例
- 晚安：这么晚还在看手机呀，记得早点休息。
- 早安：早安，新的一天，慢慢来就好。
- 低谷关怀：这两天好像没怎么看到你，还好吗？
- 节日：今天是{holiday_name}，祝你节日快乐。
- 事件跟进：今天那个{event_name}，感觉怎么样？

请生成一条关怀文案："""


# ---------------------------------------------------------------------------
# 关怀服务
# ---------------------------------------------------------------------------

class CareService:
    """AI 关怀推送服务，封装所有关怀相关业务逻辑。

    依赖外部注入：
    - settings: 应用配置
    - redis: Redis 客户端
    - push_provider: 推送服务提供者
    """

    def __init__(
        self,
        settings: AppSettings,
        redis: Any,
        push_provider: PushProtocol,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
    ) -> None:
        """初始化关怀服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            push_provider: 推送服务提供者
            ai_provider: AI 服务提供者
            zhipu_api_key: 智谱 API Key
        """
        self._settings = settings
        self._redis = redis
        self._push_provider = push_provider
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key

        # AI 服务实例缓存
        self._ai_service: GLMChatService | None = None

        # 通知服务实例
        self._notification_service: NotificationService | None = None

        logger.info(
            "[CareService] 初始化完成，AI Provider: %s",
            ai_provider,
        )

    def _get_ai_service(self) -> GLMChatService:
        """获取 AI 服务实例（使用 GLM-4-Flash 降低成本）。"""
        if self._ai_service is None:
            self._ai_service = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                model="glm-4-flash",  # 使用低成本模型
                personality="xiaowen",  # 使用温和的小温性格
            )
        return self._ai_service

    def _get_notification_service(self) -> NotificationService:
        """获取通知服务实例。"""
        if self._notification_service is None:
            self._notification_service = NotificationService(
                settings=self._settings,
                redis=self._redis,
                push_provider=self._push_provider,
            )
        return self._notification_service

    # =========================================================================
    # 频率控制
    # =========================================================================

    async def _check_care_frequency(
        self,
        user_id: str,
        care_type: str,
    ) -> bool:
        """检查关怀推送频率是否超限。

        Args:
            user_id: 用户ID
            care_type: 关怀类型

        Returns:
            是否允许推送
        """
        config = CARE_FREQUENCY_LIMITS.get(care_type)
        if not config:
            return True

        period = config["period"]
        max_count = config["max_count"]

        # 计算时间窗口
        if period == "day":
            period_key = date.today().isoformat()
        elif period == "week":
            # 获取本周起始日期（周一）
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            period_key = week_start.isoformat()
        elif period == "month":
            period_key = f"{date.today().year}-{date.today().month:02d}"
        else:
            return True

        key = REDIS_KEY_CARE_FREQUENCY.format(
            user_id=user_id,
            care_type=care_type,
            period=period_key,
        )

        current_count = await self._redis.get(key)
        if current_count is None:
            return True

        # 处理 bytes 类型（取决于 Redis 客户端配置）
        if isinstance(current_count, bytes):
            current_count = current_count.decode()

        return int(current_count) < max_count

    async def _record_care_sent(
        self,
        user_id: str,
        care_type: str,
    ) -> None:
        """记录关怀推送发送。

        Args:
            user_id: 用户ID
            care_type: 关怀类型
        """
        config = CARE_FREQUENCY_LIMITS.get(care_type)
        if not config:
            return

        period = config["period"]

        # 计算时间窗口和过期时间
        if period == "day":
            period_key = date.today().isoformat()
            ttl = 86400 * 2  # 2 天
        elif period == "week":
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            period_key = week_start.isoformat()
            ttl = 86400 * 8  # 8 天
        elif period == "month":
            period_key = f"{date.today().year}-{date.today().month:02d}"
            ttl = 86400 * 32  # 32 天
        else:
            return

        key = REDIS_KEY_CARE_FREQUENCY.format(
            user_id=user_id,
            care_type=care_type,
            period=period_key,
        )

        current = await self._redis.get(key)
        if current is None:
            await self._redis.setex(key, ttl, 1)
        else:
            await self._redis.incr(key)

    async def _is_already_sent_today(
        self,
        user_id: str,
        care_type: str,
    ) -> bool:
        """检查今天是否已发送过指定类型的关怀。

        Args:
            user_id: 用户ID
            care_type: 关怀类型

        Returns:
            是否已发送
        """
        key = REDIS_KEY_CARE_SENT_TODAY.format(
            user_id=user_id,
            care_type=care_type,
            date=date.today().isoformat(),
        )

        return bool(await self._redis.exists(key))

    async def _mark_sent_today(
        self,
        user_id: str,
        care_type: str,
    ) -> None:
        """标记今天已发送指定类型的关怀。

        Args:
            user_id: 用户ID
            care_type: 关怀类型
        """
        key = REDIS_KEY_CARE_SENT_TODAY.format(
            user_id=user_id,
            care_type=care_type,
            date=date.today().isoformat(),
        )
        await self._redis.setex(key, 86400, "1")

    # =========================================================================
    # 用户筛选
    # =========================================================================

    async def _get_active_users(
        self,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 1000,
    ) -> list[User]:
        """获取指定时间内活跃的用户列表。

        Args:
            db: 数据库会话
            hours: 活跃时间窗口（小时）
            limit: 最大返回数量

        Returns:
            活跃用户列表
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(User)
            .where(
                User.deleted_at.is_(None),
                User.last_active_at.isnot(None),
                User.last_active_at >= cutoff_time,
            )
            .order_by(User.last_active_at.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _get_inactive_users_with_negative_mood(
        self,
        db: AsyncSession,
        inactive_days: int = 2,
        recent_days: int = 7,
        limit: int = 500,
    ) -> list[User]:
        """获取连续未登录且近期情绪负面的用户。

        Args:
            db: 数据库会话
            inactive_days: 未登录天数
            recent_days: 近期天数（用于判断情绪）
            limit: 最大返回数量

        Returns:
            用户列表
        """
        inactive_cutoff = datetime.now(timezone.utc) - timedelta(days=inactive_days)
        mood_cutoff = date.today() - timedelta(days=recent_days)

        # 负面情绪基调列表
        negative_tones = ["sad", "anxious", "angry", "blue", "purple"]

        # 使用子查询一次性获取符合条件的用户，避免 N+1 查询
        # 查询近期有负面情绪日记且连续未登录的用户
        subquery = (
            select(EmotionDiary.user_id)
            .where(
                EmotionDiary.deleted_at.is_(None),
                EmotionDiary.record_date >= mood_cutoff,
                EmotionDiary.emotion_tone.in_(negative_tones),
            )
            .distinct()
        )

        stmt = (
            select(User)
            .where(
                User.deleted_at.is_(None),
                User.last_active_at.is_(None) | (User.last_active_at < inactive_cutoff),
                User.id.in_(subquery),
            )
            .limit(limit)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _get_users_with_event_today(
        self,
        db: AsyncSession,
        event_keywords: list[str],
        days_ago: int = 7,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """获取近期提到重要事件且事件发生在今天的用户。

        Args:
            db: 数据库会话
            event_keywords: 事件关键词列表
            days_ago: 查询最近多少天的对话
            limit: 最大返回数量

        Returns:
            用户事件信息列表 [{"user": User, "event_name": str, "event_date": date}]
        """
        cutoff_date = date.today() - timedelta(days=days_ago)

        # 查询 AI 记忆中的事件类型记忆
        stmt = (
            select(AIMemory)
            .where(
                AIMemory.memory_type == "event",
                AIMemory.key_facts.isnot(None),
            )
            .limit(limit * 2)
        )

        result = await db.execute(stmt)
        memories = list(result.scalars().all())

        # 筛选今天有事件的用户
        user_events = []
        today = date.today()

        for memory in memories:
            key_facts = memory.key_facts or {}
            event_date_str = key_facts.get("event_date")
            event_name = key_facts.get("event_name", "重要事件")

            if event_date_str:
                try:
                    event_date = date.fromisoformat(event_date_str)
                    if event_date == today:
                        # 获取用户信息
                        user_stmt = select(User).where(
                            User.id == memory.user_id,
                            User.deleted_at.is_(None),
                        )
                        user_result = await db.execute(user_stmt)
                        user = user_result.scalar_one_or_none()
                        if user:
                            user_events.append({
                                "user": user,
                                "event_name": event_name,
                                "event_date": event_date,
                            })
                except (ValueError, TypeError):
                    continue

        return user_events

    # =========================================================================
    # 文案生成
    # =========================================================================

    async def _generate_care_message(
        self,
        user: User,
        care_type: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """生成个性化的关怀推送文案。

        Args:
            user: 用户对象
            care_type: 关怀类型
            context: 上下文信息（如节日名称、事件名称等）

        Returns:
            关怀文案
        """
        care_type_desc = {
            CareType.GOOD_NIGHT: "晚安问候，用户在深夜时段活跃过",
            CareType.GOOD_MORNING: "早安问候，用户昨晚聊过情绪话题",
            CareType.LOW_MOOD: "情绪低谷关怀，用户连续多天未登录且近期情绪负面",
            CareType.HOLIDAY: f"节日问候，今天是{context.get('holiday_name', '特殊日子') if context else '节日'}",
            CareType.EVENT_FOLLOW: f"重要事件跟进，用户提到了{context.get('event_name', '重要事件') if context else '某件事'}",
        }

        # 获取用户最近情绪状态
        recent_mood = "暂无记录"
        if context and context.get("recent_mood"):
            recent_mood = context["recent_mood"]

        prompt = CARE_PROMPT_TEMPLATE.format(
            nickname=user.nickname or "用户",
            recent_mood=recent_mood,
            care_type_desc=care_type_desc.get(care_type, "一般关怀"),
            holiday_name=context.get("holiday_name", "") if context else "",
            event_name=context.get("event_name", "") if context else "",
        )

        try:
            ai_service = self._get_ai_service()
            response = await ai_service.chat(prompt=prompt, context={})
            # 清理响应
            message = response.strip().strip('"').strip("'")
            # 限制长度（Prompt 要求 30 字以内，这里放宽到 50 字作为安全边界）
            if len(message) > 50:
                message = message[:47] + "..."
            return message
        except Exception as e:
            logger.error("[CareService] AI 生成文案失败: %s", str(e))
            # 降级：使用默认文案
            return self._get_fallback_message(care_type, context)

    def _get_fallback_message(
        self,
        care_type: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """获取降级关怀文案（AI 生成失败时使用）。

        Args:
            care_type: 关怀类型
            context: 上下文信息

        Returns:
            默认关怀文案
        """
        fallback_messages = {
            CareType.GOOD_NIGHT: [
                "夜深了，记得早点休息。",
                "晚安，愿你今晚好眠。",
                "这么晚还在忙碌，记得照顾好自己。",
            ],
            CareType.GOOD_MORNING: [
                "早安，新的一天慢慢来。",
                "早安，愿你今天心情愉快。",
                "新的一天，从照顾好自己开始。",
            ],
            CareType.LOW_MOOD: [
                "这两天没怎么看到你，还好吗？",
                "好久不见，希望你一切都好。",
                "如果你需要聊聊，我一直都在。",
            ],
            CareType.HOLIDAY: [
                f"今天是{context.get('holiday_name', '节日')}，祝你节日快乐。" if context else "祝你节日快乐。",
            ],
            CareType.EVENT_FOLLOW: [
                f"今天那个{context.get('event_name', '事情')}，感觉怎么样？" if context else "今天感觉怎么样？",
            ],
        }

        messages = fallback_messages.get(care_type, ["希望你一切都好。"])
        return random.choice(messages)

    # =========================================================================
    # 推送发送
    # =========================================================================

    async def _send_care_notification(
        self,
        user: User,
        title: str,
        content: str,
        notification_type: str = NotificationType.AI_CARE,
        payload: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> bool:
        """发送关怀推送通知。

        Args:
            user: 用户对象
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型
            payload: 附加数据
            db: 数据库会话（可选，用于保存通知记录）

        Returns:
            是否发送成功
        """
        try:
            # 创建通知记录（如果有数据库会话）
            if db:
                notification = Notification(
                    user_id=user.id,
                    type=notification_type,
                    title=title,
                    content=content,
                    payload=payload,
                    is_read=False,
                )
                db.add(notification)
                await db.flush()

            # 直接使用推送服务发送
            push_result = await self._push_provider.send(
                user_id=user.id,
                title=title,
                content=content,
                payload=payload,
            )

            return push_result.get("success", False)

        except Exception as e:
            logger.error(
                "[CareService] 发送关怀推送失败，用户: %s，错误: %s",
                user.id, str(e)
            )
            return False

    # =========================================================================
    # 核心推送方法
    # =========================================================================

    async def send_good_night_care(
        self,
        db: AsyncSession,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """发送晚安问候推送。

        扫描过去 24 小时内活跃的用户，随机选择一部分发送晚安问候。
        时间窗口：22:30-23:30，每周最多 3 次。

        Args:
            db: 数据库会话
            batch_size: 批量处理数量

        Returns:
            推送统计
        """
        stats = {"success": 0, "skipped": 0, "failed": 0}

        # 获取活跃用户
        users = await self._get_active_users(db, hours=24, limit=batch_size)

        for user in users:
            try:
                # 检查频率限制
                if not await self._check_care_frequency(user.id, CareType.GOOD_NIGHT):
                    stats["skipped"] += 1
                    continue

                # 检查今天是否已发送
                if await self._is_already_sent_today(user.id, CareType.GOOD_NIGHT):
                    stats["skipped"] += 1
                    continue

                # 生成文案
                content = await self._generate_care_message(user, CareType.GOOD_NIGHT)

                # 发送推送
                success = await self._send_care_notification(
                    user=user,
                    title="晚安",
                    content=content,
                    notification_type=NotificationType.AI_CARE,
                    payload={"care_type": CareType.GOOD_NIGHT},
                    db=db,
                )

                if success:
                    await self._record_care_sent(user.id, CareType.GOOD_NIGHT)
                    await self._mark_sent_today(user.id, CareType.GOOD_NIGHT)
                    stats["success"] += 1
                    logger.info(
                        "[CareService] 晚安问候发送成功，用户: %s",
                        user.id,
                    )
                else:
                    stats["failed"] += 1

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "[CareService] 晚安问候发送失败，用户: %s，错误: %s",
                    user.id, str(e),
                )

        logger.info(
            "[CareService] 晚安问候任务完成，成功: %d，跳过: %d，失败: %d",
            stats["success"], stats["skipped"], stats["failed"],
        )

        return stats

    async def send_good_morning_care(
        self,
        db: AsyncSession,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """发送早安问候推送。

        扫描过去 24 小时内活跃且昨晚聊过情绪话题的用户。
        时间窗口：7:00-8:00，每周最多 2 次。

        Args:
            db: 数据库会话
            batch_size: 批量处理数量

        Returns:
            推送统计
        """
        stats = {"success": 0, "skipped": 0, "failed": 0}

        # 获取活跃用户
        users = await self._get_active_users(db, hours=24, limit=batch_size)

        for user in users:
            try:
                # 检查频率限制
                if not await self._check_care_frequency(user.id, CareType.GOOD_MORNING):
                    stats["skipped"] += 1
                    continue

                # 检查今天是否已发送
                if await self._is_already_sent_today(user.id, CareType.GOOD_MORNING):
                    stats["skipped"] += 1
                    continue

                # 生成文案
                content = await self._generate_care_message(user, CareType.GOOD_MORNING)

                # 发送推送
                success = await self._send_care_notification(
                    user=user,
                    title="早安",
                    content=content,
                    notification_type=NotificationType.AI_CARE,
                    payload={"care_type": CareType.GOOD_MORNING},
                    db=db,
                )

                if success:
                    await self._record_care_sent(user.id, CareType.GOOD_MORNING)
                    await self._mark_sent_today(user.id, CareType.GOOD_MORNING)
                    stats["success"] += 1
                    logger.info(
                        "[CareService] 早安问候发送成功，用户: %s",
                        user.id,
                    )
                else:
                    stats["failed"] += 1

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "[CareService] 早安问候发送失败，用户: %s，错误: %s",
                    user.id, str(e),
                )

        logger.info(
            "[CareService] 早安问候任务完成，成功: %d，跳过: %d，失败: %d",
            stats["success"], stats["skipped"], stats["failed"],
        )

        return stats

    async def send_low_mood_care(
        self,
        db: AsyncSession,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """发送情绪低谷关怀推送。

        检查连续 2 天未登录且近期情绪负面的用户。
        时间：每天 10:00，每月最多 2 次。

        Args:
            db: 数据库会话
            batch_size: 批量处理数量

        Returns:
            推送统计
        """
        stats = {"success": 0, "skipped": 0, "failed": 0}

        # 获取符合条件的目标用户
        users = await self._get_inactive_users_with_negative_mood(
            db,
            inactive_days=2,
            recent_days=7,
            limit=batch_size,
        )

        for user in users:
            try:
                # 检查频率限制
                if not await self._check_care_frequency(user.id, CareType.LOW_MOOD):
                    stats["skipped"] += 1
                    continue

                # 检查今天是否已发送
                if await self._is_already_sent_today(user.id, CareType.LOW_MOOD):
                    stats["skipped"] += 1
                    continue

                # 生成文案
                content = await self._generate_care_message(user, CareType.LOW_MOOD)

                # 发送推送
                success = await self._send_care_notification(
                    user=user,
                    title="好久不见",
                    content=content,
                    notification_type=NotificationType.AI_CARE,
                    payload={"care_type": CareType.LOW_MOOD},
                    db=db,
                )

                if success:
                    await self._record_care_sent(user.id, CareType.LOW_MOOD)
                    await self._mark_sent_today(user.id, CareType.LOW_MOOD)
                    stats["success"] += 1
                    logger.info(
                        "[CareService] 情绪低谷关怀发送成功，用户: %s",
                        user.id,
                    )
                else:
                    stats["failed"] += 1

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "[CareService] 情绪低谷关怀发送失败，用户: %s，错误: %s",
                    user.id, str(e),
                )

        logger.info(
            "[CareService] 情绪低谷关怀任务完成，成功: %d，跳过: %d，失败: %d",
            stats["success"], stats["skipped"], stats["failed"],
        )

        return stats

    async def send_holiday_care(
        self,
        db: AsyncSession,
        target_date: date | None = None,
        batch_size: int = 1000,
    ) -> dict[str, int]:
        """发送节日问候推送。

        查询当天是否有节日，有则给所有活跃用户发送问候。
        时间：节日当天 10:00。

        Args:
            db: 数据库会话
            target_date: 目标日期，默认今天
            batch_size: 批量处理数量

        Returns:
            推送统计
        """
        stats = {"success": 0, "skipped": 0, "failed": 0, "holidays": 0}

        if target_date is None:
            target_date = date.today()

        # 查询今天的节日
        stmt = (
            select(Holiday)
            .where(
                Holiday.is_active == True,  # noqa: E712
                Holiday.month == target_date.month,
                Holiday.day == target_date.day,
            )
        )

        result = await db.execute(stmt)
        holidays = list(result.scalars().all())

        if not holidays:
            logger.info(
                "[CareService] 今天没有节日，跳过节日问候推送"
            )
            return stats

        stats["holidays"] = len(holidays)

        # 获取活跃用户
        users = await self._get_active_users(db, hours=168, limit=batch_size)  # 近一周活跃

        for holiday in holidays:
            for user in users:
                try:
                    # 检查今天是否已发送该节日的问候
                    holiday_key = f"{CareType.HOLIDAY}:{holiday.id}"
                    if await self._is_already_sent_today(user.id, holiday_key):
                        stats["skipped"] += 1
                        continue

                    # 生成文案
                    context = {"holiday_name": holiday.name}
                    if holiday.greeting_template:
                        # 使用模板生成文案
                        content = holiday.greeting_template.format(name=user.nickname or "你")
                    else:
                        content = await self._generate_care_message(
                            user, CareType.HOLIDAY, context
                        )

                    # 发送推送
                    success = await self._send_care_notification(
                        user=user,
                        title=f"{holiday.name}快乐",
                        content=content,
                        notification_type=NotificationType.AI_CARE,
                        payload={
                            "care_type": CareType.HOLIDAY,
                            "holiday_id": holiday.id,
                            "holiday_name": holiday.name,
                        },
                        db=db,
                    )

                    if success:
                        await self._mark_sent_today(user.id, holiday_key)
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1

                except Exception as e:
                    stats["failed"] += 1
                    logger.error(
                        "[CareService] 节日问候发送失败，用户: %s，节日: %s，错误: %s",
                        user.id, holiday.name, str(e),
                    )

        logger.info(
            "[CareService] 节日问候任务完成，节日数: %d，成功: %d，跳过: %d，失败: %d",
            stats["holidays"], stats["success"], stats["skipped"], stats["failed"],
        )

        return stats

    async def send_event_follow_care(
        self,
        db: AsyncSession,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """发送重要事件跟进推送。

        检查用户近期提到的面试/考试等重要事件，在事件当天晚上发送跟进。
        时间：事件当天晚上 20:00。

        Args:
            db: 数据库会话
            batch_size: 批量处理数量

        Returns:
            推送统计
        """
        stats = {"success": 0, "skipped": 0, "failed": 0, "events": 0}

        # 获取今天有事件的用户
        user_events = await self._get_users_with_event_today(
            db,
            event_keywords=["面试", "考试", "答辩", "汇报", "演讲", "约会", "见面"],
            days_ago=7,
            limit=batch_size,
        )

        stats["events"] = len(user_events)

        for event_info in user_events:
            user = event_info["user"]
            event_name = event_info["event_name"]

            try:
                # 检查今天是否已发送该事件的跟进
                event_key = f"{CareType.EVENT_FOLLOW}:{event_name}"
                if await self._is_already_sent_today(user.id, event_key):
                    stats["skipped"] += 1
                    continue

                # 生成文案
                context = {"event_name": event_name}
                content = await self._generate_care_message(
                    user, CareType.EVENT_FOLLOW, context
                )

                # 发送推送
                success = await self._send_care_notification(
                    user=user,
                    title="想问问你",
                    content=content,
                    notification_type=NotificationType.AI_CARE,
                    payload={
                        "care_type": CareType.EVENT_FOLLOW,
                        "event_name": event_name,
                    },
                    db=db,
                )

                if success:
                    await self._mark_sent_today(user.id, event_key)
                    stats["success"] += 1
                    logger.info(
                        "[CareService] 事件跟进发送成功，用户: %s，事件: %s",
                        user.id, event_name,
                    )
                else:
                    stats["failed"] += 1

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "[CareService] 事件跟进发送失败，用户: %s，错误: %s",
                    user.id, str(e),
                )

        logger.info(
            "[CareService] 事件跟进任务完成，事件数: %d，成功: %d，跳过: %d，失败: %d",
            stats["events"], stats["success"], stats["skipped"], stats["failed"],
        )

        return stats

    async def send_user_holiday_care(
        self,
        db: AsyncSession,
        target_date: date | None = None,
        batch_size: int = 500,
    ) -> dict[str, int]:
        """发送用户自定义节日问候推送。

        查询用户自定义的节日（如生日、纪念日），在当天发送问候。

        Args:
            db: 数据库会话
            target_date: 目标日期，默认今天
            batch_size: 批量处理数量

        Returns:
            推送统计
        """
        stats = {"success": 0, "skipped": 0, "failed": 0, "holidays": 0}

        if target_date is None:
            target_date = date.today()

        # 查询今天的用户自定义节日
        stmt = (
            select(UserHoliday)
            .where(
                UserHoliday.reminder_enabled == True,  # noqa: E712
                UserHoliday.month == target_date.month,
                UserHoliday.day == target_date.day,
            )
            .limit(batch_size)
        )

        result = await db.execute(stmt)
        user_holidays = list(result.scalars().all())

        if not user_holidays:
            logger.info(
                "[CareService] 今天没有用户自定义节日，跳过"
            )
            return stats

        stats["holidays"] = len(user_holidays)

        for user_holiday in user_holidays:
            try:
                # 获取用户
                user_stmt = select(User).where(
                    User.id == user_holiday.user_id,
                    User.deleted_at.is_(None),
                )
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()

                if not user:
                    stats["skipped"] += 1
                    continue

                # 检查今天是否已发送
                holiday_key = f"user_holiday:{user_holiday.id}"
                if await self._is_already_sent_today(user.id, holiday_key):
                    stats["skipped"] += 1
                    continue

                # 生成文案
                context = {"holiday_name": user_holiday.name}
                content = await self._generate_care_message(
                    user, CareType.HOLIDAY, context
                )

                # 发送推送
                success = await self._send_care_notification(
                    user=user,
                    title=f"{user_holiday.name}快乐",
                    content=content,
                    notification_type=NotificationType.AI_CARE,
                    payload={
                        "care_type": "user_holiday",
                        "user_holiday_id": user_holiday.id,
                        "holiday_name": user_holiday.name,
                    },
                    db=db,
                )

                if success:
                    await self._mark_sent_today(user.id, holiday_key)
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "[CareService] 用户自定义节日问候发送失败，节日ID: %s，错误: %s",
                    user_holiday.id, str(e),
                )

        logger.info(
            "[CareService] 用户自定义节日问候任务完成，节日数: %d，成功: %d，跳过: %d，失败: %d",
            stats["holidays"], stats["success"], stats["skipped"], stats["failed"],
        )

        return stats

    # =========================================================================
    # 社交能量重置
    # =========================================================================

    async def reset_social_energy(
        self,
        db: AsyncSession,
        batch_size: int = 1000,
    ) -> dict[str, int]:
        """重置所有用户的社交能量值。

        每日 00:00 执行，将所有用户的 social_energy 重置为 50。

        Args:
            db: 数据库会话
            batch_size: 批量处理数量

        Returns:
            重置统计
        """
        from sqlalchemy import update

        stats = {"success": 0, "failed": 0}

        try:
            now = datetime.now(timezone.utc)

            # 批量更新所有用户的社交能量
            stmt = (
                update(User)
                .where(User.deleted_at.is_(None))
                .values(social_energy=50, social_energy_updated_at=now)
            )

            result = await db.execute(stmt)
            await db.commit()

            stats["success"] = result.rowcount

            logger.info(
                "[CareService] 社交能量重置完成，影响用户数: %d",
                stats["success"],
            )

        except Exception as e:
            stats["failed"] = 1
            logger.error(
                "[CareService] 社交能量重置失败: %s",
                str(e),
            )

        return stats
