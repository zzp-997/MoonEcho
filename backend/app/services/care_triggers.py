"""事件驱动关怀触发服务。

基于用户行为事件，触发 AI 主动关怀推送：
- 好友申请通过后发送关怀推送
- 评论获得共鸣后发送通知
- 情绪周报生成完成后通知用户

核心设计原则：
1. 宁可漏发不可滥发 - 频率控制严格
2. 用户可关闭非危机推送
3. 危机干预推送强制开启，不可关闭
4. AI 生成个性化推送文案（GLM-4-Flash）
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationType
from app.services.ai_chat import MockAIChat, GLMChatService, create_ai_chat_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

REDIS_KEY_EVENT_CARE_FREQ = "care:event:{user_id}:{event_type}:{period}"
REDIS_KEY_EVENT_CARE_SENT_TODAY = "care:event:sent:{user_id}:{event_type}:{date}"


# ---------------------------------------------------------------------------
# 事件类型定义
# ---------------------------------------------------------------------------

class CareEventType(str, Enum):
    """关怀触发事件类型。"""

    FRIEND_ACCEPT = "friend_accept"        # 好友申请通过
    RESONANCE_GAINED = "resonance_gained"  # 评论获得共鸣
    WEEKLY_REPORT_READY = "weekly_report"  # 情绪周报生成完成
    CRISIS_DETECTED = "crisis_detected"    # 危机内容检测


# ---------------------------------------------------------------------------
# 事件频率限制配置
# ---------------------------------------------------------------------------

EVENT_CARE_FREQUENCY_LIMITS = {
    CareEventType.FRIEND_ACCEPT: {"max_count": 1, "period": "day"},
    CareEventType.RESONANCE_GAINED: {"max_count": 3, "period": "day"},
    CareEventType.WEEKLY_REPORT_READY: {"max_count": 1, "period": "week"},
    CareEventType.CRISIS_DETECTED: {"max_count": 99, "period": "day"},  # 危机无限制
}

# 危机事件类型集合（强制开启）
CRISIS_EVENT_TYPES = {CareEventType.CRISIS_DETECTED}


# ---------------------------------------------------------------------------
# 关怀文案 Prompt 模板
# ---------------------------------------------------------------------------

EVENT_CARE_PROMPT_TEMPLATE = """你是一个温暖的 AI 陪伴助手，正在为用户生成一条简短的通知推送文案。

## 用户信息
- 昵称：{nickname}

## 事件类型
{event_type_desc}

## 上下文信息
{context_desc}

## 输出要求
1. 文案长度控制在 25 字以内
2. 语气温和、不评判、不说教
3. 不要使用感叹号，避免过度热情
4. 不要使用"你应该""你需要"等命令式语言
5. 针对事件类型给出个性化文案
6. 输出纯文本，不要包含任何 Markdown 格式

## 示例
- 好友通过：你们现在是好友了，有空聊聊吧。
- 获得共鸣：有人在树洞里懂你，去看看吧。
- 周报完成：这周的情绪记录出来了，来看看吧。
- 危机关怀：我在，你愿意跟我说说吗？

请生成一条推送文案："""


EVENT_TYPE_DESCRIPTIONS = {
    CareEventType.FRIEND_ACCEPT: "好友申请已通过，用户获得了新的好友",
    CareEventType.RESONANCE_GAINED: "用户的树洞吐槽收到了他人的共鸣",
    CareEventType.WEEKLY_REPORT_READY: "用户的情绪周报已生成完成",
    CareEventType.CRISIS_DETECTED: "检测到用户发布了危机相关内容，需要主动关怀",
}

DEFAULT_CONTEXT_DESC = "无额外上下文"


# ---------------------------------------------------------------------------
# 默认关怀文案（降级使用）
# ---------------------------------------------------------------------------

DEFAULT_CARE_MESSAGES = {
    CareEventType.FRIEND_ACCEPT: [
        "你们现在是好友了，有空聊聊吧。",
        "好友通过了，说声嗨？",
        "新朋友诶，去打个招呼吧。",
    ],
    CareEventType.RESONANCE_GAINED: [
        "有人在树洞里懂你，去看看吧。",
        "有人点了共鸣，你的话说到了别人心里。",
        "有人懂你，去看看？",
    ],
    CareEventType.WEEKLY_REPORT_READY: [
        "这周的情绪记录出来了，来看看吧。",
        "周报准备好了，看看这周的你。",
        "情绪周报来了，看看吧。",
    ],
    CareEventType.CRISIS_DETECTED: [
        "我在，你愿意跟我说说吗？",
        "如果你需要聊聊，我一直都在。",
        "感觉到你可能不太好，我在这。",
    ],
}


# ---------------------------------------------------------------------------
# 推送服务接口
# ---------------------------------------------------------------------------

class PushProviderProtocol(Protocol):
    """推送服务接口协议。"""

    async def send(
        self,
        user_id: str,
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送推送通知。

        Args:
            user_id: 用户 ID
            title: 推送标题
            content: 推送内容
            payload: 附加数据

        Returns:
            推送结果
        """
        ...


# ---------------------------------------------------------------------------
# 事件驱动关怀触发服务
# ---------------------------------------------------------------------------

class CareTriggerService:
    """事件驱动关怀触发服务。

    根据用户行为事件触发相应的 AI 主动关怀推送。
    支持频率控制、个性化文案生成、危机强制推送。

    使用示例：
        service = CareTriggerService(settings, redis, push_provider)

        # 触发好友通过关怀
        await service.trigger_friend_accept_care(
            user_id="xxx",
            friend_name="月亮收集者",
            db=db
        )

        # 触发共鸣通知
        await service.trigger_resonance_care(
            user_id="xxx",
            post_content="今天好累...",
            resonance_count=3,
            db=db
        )
    """

    def __init__(
        self,
        settings: Any,
        redis: Any,
        push_provider: PushProviderProtocol,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
    ) -> None:
        """初始化事件驱动关怀触发服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            push_provider: 推送服务提供者
            ai_provider: AI 服务提供者（mock/glm_free/glm）
            zhipu_api_key: 智谱 API Key
        """
        self._settings = settings
        self._redis = redis
        self._push_provider = push_provider
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key

        # AI 服务实例缓存
        self._ai_service: MockAIChat | GLMChatService | None = None

        logger.info(
            "[CareTriggerService] 初始化完成，AI Provider: %s",
            ai_provider
        )

    def _get_ai_service(self) -> MockAIChat | GLMChatService:
        """获取 AI 服务实例（使用 GLM-4-Flash 降低成本）。"""
        if self._ai_service is None:
            self._ai_service = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                model="glm-4-flash",  # 使用低成本模型
                personality="xiaowen",  # 使用温和的小温性格
            )
        return self._ai_service

    # =========================================================================
    # 频率控制
    # =========================================================================

    async def _check_event_frequency(
        self,
        user_id: str,
        event_type: CareEventType,
    ) -> bool:
        """检查事件触发频率是否超限。

        Args:
            user_id: 用户 ID
            event_type: 事件类型

        Returns:
            是否允许推送
        """
        # 危机事件不受频率限制
        if event_type in CRISIS_EVENT_TYPES:
            return True

        config = EVENT_CARE_FREQUENCY_LIMITS.get(event_type)
        if not config:
            return True

        period = config["period"]
        max_count = config["max_count"]

        # 计算时间窗口
        if period == "day":
            period_key = datetime.now().strftime("%Y-%m-%d")
        elif period == "week":
            today = datetime.now()
            week_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = week_start - timedelta(days=today.weekday())
            period_key = week_start.strftime("%Y-%m-%d")
        else:
            return True

        key = REDIS_KEY_EVENT_CARE_FREQ.format(
            user_id=user_id,
            event_type=event_type.value,
            period=period_key,
        )

        current_count = await self._redis.get(key)
        if current_count is None:
            return True

        # 处理 bytes 类型并安全转换
        try:
            if isinstance(current_count, bytes):
                current_count = current_count.decode()
            count = int(current_count)
        except (ValueError, TypeError):
            # 缓存数据格式异常，重置计数
            logger.warning(
                "[CareTriggerService] Redis 计数器数据格式异常，重置: %s",
                current_count
            )
            return True

        return count < max_count

    async def _record_event_sent(
        self,
        user_id: str,
        event_type: CareEventType,
    ) -> None:
        """记录事件触发推送发送。

        Args:
            user_id: 用户 ID
            event_type: 事件类型
        """
        config = EVENT_CARE_FREQUENCY_LIMITS.get(event_type)
        if not config:
            return

        period = config["period"]

        # 计算时间窗口和过期时间
        if period == "day":
            period_key = datetime.now().strftime("%Y-%m-%d")
            ttl = 86400 * 2  # 2 天
        elif period == "week":
            today = datetime.now()
            week_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = week_start - timedelta(days=today.weekday())
            period_key = week_start.strftime("%Y-%m-%d")
            ttl = 86400 * 8  # 8 天
        else:
            return

        key = REDIS_KEY_EVENT_CARE_FREQ.format(
            user_id=user_id,
            event_type=event_type.value,
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
        event_type: CareEventType,
    ) -> bool:
        """检查今天是否已发送过指定类型的事件关怀。

        Args:
            user_id: 用户 ID
            event_type: 事件类型

        Returns:
            是否已发送
        """
        # 危机事件可以重复发送
        if event_type in CRISIS_EVENT_TYPES:
            return False

        key = REDIS_KEY_EVENT_CARE_SENT_TODAY.format(
            user_id=user_id,
            event_type=event_type.value,
            date=datetime.now().strftime("%Y-%m-%d"),
        )

        return bool(await self._redis.exists(key))

    async def _mark_sent_today(
        self,
        user_id: str,
        event_type: CareEventType,
    ) -> None:
        """标记今天已发送指定类型的事件关怀。

        Args:
            user_id: 用户 ID
            event_type: 事件类型
        """
        key = REDIS_KEY_EVENT_CARE_SENT_TODAY.format(
            user_id=user_id,
            event_type=event_type.value,
            date=datetime.now().strftime("%Y-%m-%d"),
        )
        await self._redis.setex(key, 86400, "1")

    # =========================================================================
    # 用户通知偏好检查
    # =========================================================================

    async def _is_care_enabled(self, user_id: str, event_type: CareEventType) -> bool:
        """检查用户是否开启了指定类型的关怀推送。

        危机干预推送强制开启，不可关闭。

        Args:
            user_id: 用户 ID
            event_type: 事件类型

        Returns:
            是否允许推送
        """
        # 危机干预强制开启
        if event_type in CRISIS_EVENT_TYPES:
            return True

        # 从 Redis 缓存获取用户通知设置
        settings_key = f"notification:settings:{user_id}"
        cached = await self._redis.get(settings_key)

        if cached:
            try:
                # 处理 bytes 类型
                if isinstance(cached, bytes):
                    cached = cached.decode("utf-8")
                settings = json.loads(cached)
                if not settings.get("push_enabled", True):
                    return False
                # AI 关怀推送开关
                return settings.get("types_enabled", {}).get(NotificationType.AI_CARE, True)
            except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as e:
                logger.warning(
                    "[CareTriggerService] 解析用户通知设置缓存失败，用户: %s，错误: %s",
                    user_id, str(e)
                )
                # 缓存数据异常时返回默认值

        # 默认开启
        return True

    # =========================================================================
    # 文案生成
    # =========================================================================

    async def _generate_care_message(
        self,
        user: User,
        event_type: CareEventType,
        context: dict[str, Any] | None = None,
    ) -> str:
        """生成个性化的事件关怀文案。

        Args:
            user: 用户对象
            event_type: 事件类型
            context: 上下文信息

        Returns:
            关怀文案
        """
        event_type_desc = EVENT_TYPE_DESCRIPTIONS.get(
            event_type, "一般事件"
        )

        context_desc = DEFAULT_CONTEXT_DESC
        if context:
            context_parts = []
            if context.get("friend_name"):
                context_parts.append(f"好友昵称：{context['friend_name']}")
            if context.get("resonance_count"):
                context_parts.append(f"共鸣数：{context['resonance_count']}")
            if context.get("post_preview"):
                preview = context["post_preview"][:50]
                context_parts.append(f"帖子预览：{preview}...")
            if context_parts:
                context_desc = "\n".join(context_parts)

        prompt = EVENT_CARE_PROMPT_TEMPLATE.format(
            nickname=user.nickname or "用户",
            event_type_desc=event_type_desc,
            context_desc=context_desc,
        )

        try:
            ai_service = self._get_ai_service()
            response = await ai_service.chat(prompt, context={})
            # 清理响应
            message = response.strip().strip('"').strip("'")
            # 限制长度
            if len(message) > 35:
                message = message[:32] + "..."
            return message
        except Exception as e:
            logger.error("[CareTriggerService] AI 生成文案失败: %s", str(e))
            return self._get_fallback_message(event_type)

    def _get_fallback_message(self, event_type: CareEventType) -> str:
        """获取降级文案（AI 生成失败时使用）。

        Args:
            event_type: 事件类型

        Returns:
            默认文案
        """
        messages = DEFAULT_CARE_MESSAGES.get(
            event_type,
            ["希望你一切都好。"]
        )
        return random.choice(messages)

    # =========================================================================
    # 推送发送
    # =========================================================================

    async def _send_care_notification(
        self,
        user: User,
        title: str,
        content: str,
        event_type: CareEventType,
        payload: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> bool:
        """发送事件关怀推送通知。

        Args:
            user: 用户对象
            title: 通知标题
            content: 通知内容
            event_type: 事件类型
            payload: 附加数据
            db: 数据库会话（可选）

        Returns:
            是否发送成功
        """
        try:
            # 创建通知记录（如果有数据库会话）
            if db:
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    type=NotificationType.AI_CARE,
                    title=title,
                    content=content,
                    payload={
                        **(payload or {}),
                        "event_type": event_type.value,
                    },
                    is_read=False,
                )
                db.add(notification)
                await db.flush()

            # 发送推送
            push_result = await self._push_provider.send(
                user_id=user.id,
                title=title,
                content=content,
                payload=payload,
            )

            return push_result.get("success", False)

        except Exception as e:
            logger.error(
                "[CareTriggerService] 发送事件关怀推送失败，用户: %s，事件: %s，错误: %s",
                user.id, event_type.value, str(e)
            )
            return False

    # =========================================================================
    # 核心触发方法
    # =========================================================================

    async def trigger_friend_accept_care(
        self,
        user_id: str,
        friend_name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """触发好友申请通过后的关怀推送。

        检查频率限制和用户偏好，发送个性化关怀通知。

        Args:
            user_id: 用户 ID
            friend_name: 好友昵称
            db: 数据库会话

        Returns:
            触发结果
        """
        result = {
            "success": False,
            "skipped": False,
            "reason": None,
        }

        try:
            # 获取用户信息
            user_stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                result["reason"] = "用户不存在"
                return result

            # 检查用户偏好
            if not await self._is_care_enabled(user_id, CareEventType.FRIEND_ACCEPT):
                result["skipped"] = True
                result["reason"] = "用户已关闭此类推送"
                logger.info(
                    "[CareTriggerService] 用户 %s 已关闭好友通过推送，跳过",
                    user_id
                )
                return result

            # 检查频率限制
            if not await self._check_event_frequency(user_id, CareEventType.FRIEND_ACCEPT):
                result["skipped"] = True
                result["reason"] = "频率超限"
                return result

            # 检查今天是否已发送
            if await self._is_already_sent_today(user_id, CareEventType.FRIEND_ACCEPT):
                result["skipped"] = True
                result["reason"] = "今日已发送"
                return result

            # 生成文案
            context = {"friend_name": friend_name}
            content = await self._generate_care_message(
                user, CareEventType.FRIEND_ACCEPT, context
            )

            # 发送推送
            success = await self._send_care_notification(
                user=user,
                title="新朋友",
                content=content,
                event_type=CareEventType.FRIEND_ACCEPT,
                payload={"friend_name": friend_name},
                db=db,
            )

            if success:
                await self._record_event_sent(user_id, CareEventType.FRIEND_ACCEPT)
                await self._mark_sent_today(user_id, CareEventType.FRIEND_ACCEPT)
                result["success"] = True
                logger.info(
                    "[CareTriggerService] 好友通过关怀发送成功，用户: %s，好友: %s",
                    user_id, friend_name
                )
            else:
                result["reason"] = "推送发送失败"

        except Exception as e:
            result["reason"] = str(e)
            logger.error(
                "[CareTriggerService] 好友通过关怀发送失败，用户: %s，错误: %s",
                user_id, str(e)
            )

        return result

    async def trigger_resonance_care(
        self,
        user_id: str,
        post_id: str,
        post_content: str,
        resonance_count: int,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """触发评论获得共鸣后的通知推送。

        Args:
            user_id: 用户 ID
            post_id: 帖子 ID
            post_content: 帖子内容（用于生成文案）
            resonance_count: 共鸣数量
            db: 数据库会话

        Returns:
            触发结果
        """
        result = {
            "success": False,
            "skipped": False,
            "reason": None,
        }

        try:
            # 获取用户信息
            user_stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                result["reason"] = "用户不存在"
                return result

            # 检查用户偏好
            if not await self._is_care_enabled(user_id, CareEventType.RESONANCE_GAINED):
                result["skipped"] = True
                result["reason"] = "用户已关闭此类推送"
                return result

            # 检查频率限制
            if not await self._check_event_frequency(user_id, CareEventType.RESONANCE_GAINED):
                result["skipped"] = True
                result["reason"] = "频率超限"
                return result

            # 生成文案
            context = {
                "resonance_count": resonance_count,
                "post_preview": post_content[:50] if post_content else "",
            }
            content = await self._generate_care_message(
                user, CareEventType.RESONANCE_GAINED, context
            )

            # 发送推送
            success = await self._send_care_notification(
                user=user,
                title="有人懂你",
                content=content,
                event_type=CareEventType.RESONANCE_GAINED,
                payload={
                    "post_id": post_id,
                    "resonance_count": resonance_count,
                },
                db=db,
            )

            if success:
                await self._record_event_sent(user_id, CareEventType.RESONANCE_GAINED)
                result["success"] = True
                logger.info(
                    "[CareTriggerService] 共鸣通知发送成功，用户: %s，帖子: %s，共鸣数: %d",
                    user_id, post_id, resonance_count
                )
            else:
                result["reason"] = "推送发送失败"

        except Exception as e:
            result["reason"] = str(e)
            logger.error(
                "[CareTriggerService] 共鸣通知发送失败，用户: %s，错误: %s",
                user_id, str(e)
            )

        return result

    async def trigger_weekly_report_care(
        self,
        user_id: str,
        report_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """触发情绪周报生成完成后的通知推送。

        周报推送采用静默方式，不打扰用户。

        Args:
            user_id: 用户 ID
            report_id: 周报 ID
            db: 数据库会话

        Returns:
            触发结果
        """
        result = {
            "success": False,
            "skipped": False,
            "reason": None,
        }

        try:
            # 获取用户信息
            user_stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                result["reason"] = "用户不存在"
                return result

            # 检查用户偏好
            if not await self._is_care_enabled(user_id, CareEventType.WEEKLY_REPORT_READY):
                result["skipped"] = True
                result["reason"] = "用户已关闭此类推送"
                return result

            # 检查频率限制（每周最多 1 次）
            if not await self._check_event_frequency(user_id, CareEventType.WEEKLY_REPORT_READY):
                result["skipped"] = True
                result["reason"] = "本周已发送"
                return result

            # 生成文案
            content = await self._generate_care_message(
                user, CareEventType.WEEKLY_REPORT_READY
            )

            # 创建站内通知（周报采用静默通知，不推送）
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                type=NotificationType.WEEKLY_REPORT,
                title="情绪周报",
                content=content,
                payload={
                    "report_id": report_id,
                    "event_type": CareEventType.WEEKLY_REPORT_READY.value,
                },
                is_read=False,
            )
            db.add(notification)
            await db.flush()

            await self._record_event_sent(user_id, CareEventType.WEEKLY_REPORT_READY)
            result["success"] = True

            logger.info(
                "[CareTriggerService] 周报通知创建成功，用户: %s，周报: %s（静默通知，不打push）",
                user_id, report_id
            )

        except Exception as e:
            result["reason"] = str(e)
            logger.error(
                "[CareTriggerService] 周报通知创建失败，用户: %s，错误: %s",
                user_id, str(e)
            )

        return result

    async def trigger_crisis_care(
        self,
        user_id: str,
        crisis_level: str,
        trigger_source: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """触发危机内容检测后的紧急关怀推送。

        危机干预推送强制开启，不受频率限制，不受用户偏好影响。

        Args:
            user_id: 用户 ID
            crisis_level: 危机级别（low/medium/high）
            trigger_source: 触发来源（treehole/diary/chat）
            db: 数据库会话

        Returns:
            触发结果
        """
        result = {
            "success": False,
            "skipped": False,
            "reason": None,
        }

        try:
            # 获取用户信息
            user_stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                result["reason"] = "用户不存在"
                return result

            # 危机推送不受频率限制，直接发送

            # 生成危机关怀文案
            context = {
                "crisis_level": crisis_level,
                "trigger_source": trigger_source,
            }
            content = await self._generate_care_message(
                user, CareEventType.CRISIS_DETECTED, context
            )

            # 发送推送
            success = await self._send_care_notification(
                user=user,
                title="我在这里",
                content=content,
                event_type=CareEventType.CRISIS_DETECTED,
                payload={
                    "crisis_level": crisis_level,
                    "trigger_source": trigger_source,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                db=db,
            )

            if success:
                result["success"] = True
                logger.warning(
                    "[CareTriggerService] 危机关怀推送发送成功，用户: %s，级别: %s，来源: %s",
                    user_id, crisis_level, trigger_source
                )
            else:
                result["reason"] = "推送发送失败"

        except Exception as e:
            result["reason"] = str(e)
            logger.error(
                "[CareTriggerService] 危机关怀推送发送失败，用户: %s，错误: %s",
                user_id, str(e)
            )

        return result

    # =========================================================================
    # 批量处理方法
    # =========================================================================

    async def process_pending_events(
        self,
        db: AsyncSession,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """处理待发送的事件关怀队列。

        可由定时任务调用，批量处理积压的事件。

        Args:
            db: 数据库会话
            batch_size: 批量处理数量

        Returns:
            处理统计
        """
        # 此方法预留用于后续扩展队列处理
        stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        logger.info(
            "[CareTriggerService] 批量事件处理完成，处理: %d，成功: %d，失败: %d，跳过: %d",
            stats["processed"],
            stats["success"],
            stats["failed"],
            stats["skipped"],
        )

        return stats


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_care_trigger_service(
    settings: Any,
    redis: Any,
    push_provider: PushProviderProtocol,
    ai_provider: str = "mock",
    zhipu_api_key: str = "",
) -> CareTriggerService:
    """创建事件驱动关怀触发服务实例。

    Args:
        settings: 应用配置
        redis: Redis 客户端
        push_provider: 推送服务提供者
        ai_provider: AI 服务提供者
        zhipu_api_key: 智谱 API Key

    Returns:
        CareTriggerService 实例
    """
    return CareTriggerService(
        settings=settings,
        redis=redis,
        push_provider=push_provider,
        ai_provider=ai_provider,
        zhipu_api_key=zhipu_api_key,
    )
