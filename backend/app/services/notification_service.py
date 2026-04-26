"""通知服务模块。

提供通知管理、推送频率控制、通知合并等功能。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.notification import Notification, PushRecord
from app.models.user import User
from app.schemas.notification import (
    DEFAULT_DISABLED_TYPES,
    DEFAULT_ENABLED_TYPES,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdateRequest,
    NotificationType,
    PushFrequencyConfig,
    PushRequest,
    PushResult,
)
from app.services.push import PushProtocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 前缀定义
# ---------------------------------------------------------------------------

REDIS_KEY_PUSH_FREQUENCY = "push:freq:{user_id}:{push_type}"
REDIS_KEY_NOTIFICATION_MERGE = "push:merge:{user_id}:{notification_type}"
REDIS_KEY_NOTIFICATION_SETTINGS = "notification:settings:{user_id}"


class NotificationService:
    """通知服务。

    负责：
    - 通知的 CRUD 操作
    - 推送频率控制（Redis 缓存）
    - 通知合并（5 分钟内同类通知合并）
    - 通知设置管理
    """

    def __init__(
        self,
        settings: AppSettings,
        redis: Any,
        push_provider: PushProtocol,
    ) -> None:
        """初始化通知服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            push_provider: 推送服务提供者
        """
        self._settings = settings
        self._redis = redis
        self._push_provider = push_provider

    # =========================================================================
    # 通知 CRUD
    # =========================================================================

    async def list_notifications(
        self,
        user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
        notification_type: str | None = None,
    ) -> dict[str, Any]:
        """获取用户通知列表。

        Args:
            user_id: 用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量
            unread_only: 是否只显示未读
            notification_type: 按类型筛选

        Returns:
            分页通知列表和未读数
        """
        # 构建查询条件
        conditions = [Notification.user_id == user_id]
        if unread_only:
            conditions.append(Notification.is_read == False)  # noqa: E712
        if notification_type:
            conditions.append(Notification.type == notification_type)

        # 查询总数
        count_stmt = select(func.count()).select_from(Notification).where(*conditions)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询未读数
        unread_stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        unread_result = await db.execute(unread_stmt)
        unread_count = unread_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * page_size
        stmt = (
            select(Notification)
            .where(*conditions)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()

        return {
            "data": [NotificationResponse.model_validate(n) for n in notifications],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": page * page_size < total,
            "unread_count": unread_count,
        }

    async def mark_as_read(
        self,
        user_id: str,
        notification_id: str,
        db: AsyncSession,
    ) -> NotificationResponse:
        """标记单条通知为已读。

        Args:
            user_id: 用户ID
            notification_id: 通知ID
            db: 数据库会话

        Returns:
            更新后的通知

        Raises:
            AppError: 通知不存在或已读
        """
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            raise AppError(
                code=ErrorCode.NOTIFICATION_NOT_FOUND,
                message="通知不存在",
                status_code=404,
            )

        if notification.is_read:
            raise AppError(
                code=ErrorCode.NOTIFICATION_ALREADY_READ,
                message="通知已读",
                status_code=400,
            )

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)

        return NotificationResponse.model_validate(notification)

    async def mark_all_as_read(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, int]:
        """标记全部通知为已读。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            更新的通知数量
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True, read_at=now)
        )
        result = await db.execute(stmt)
        await db.commit()

        return {"updated_count": result.rowcount}

    # =========================================================================
    # 推送核心逻辑
    # =========================================================================

    async def send_push(
        self,
        request: PushRequest,
        db: AsyncSession,
    ) -> PushResult:
        """发送推送通知。

        包含频率控制、通知合并逻辑。

        Args:
            request: 推送请求
            db: 数据库会话

        Returns:
            推送结果
        """
        user_id = request.user_id
        push_type = request.notification_type

        # 1. 检查用户通知设置
        if not await self._is_push_enabled(user_id, push_type):
            logger.info(
                "[Notification] 用户 %s 已关闭 %s 类型推送，跳过",
                user_id, push_type,
            )
            return PushResult(
                success=False,
                error_message="用户已关闭此类通知",
            )

        # 2. 检查推送频率
        if not await self._check_push_frequency(user_id, push_type):
            logger.warning(
                "[Notification] 用户 %s %s 类型推送频率超限",
                user_id, push_type,
            )
            return PushResult(
                success=False,
                error_message="推送频率超限",
            )

        # 3. 检查是否可以合并
        merged = await self._try_merge_notification(request, db)
        if merged:
            logger.info(
                "[Notification] 用户 %s %s 类型通知已合并",
                user_id, push_type,
            )
            return PushResult(
                success=True,
                merged=True,
                merged_count=merged.merged_count,
                notification_id=merged.notification_id,
            )

        # 4. 创建通知记录
        notification = Notification(
            user_id=user_id,
            type=push_type,
            title=request.title,
            content=request.content,
            payload=request.payload,
            is_read=False,
        )
        db.add(notification)
        await db.flush()

        # 5. 发送推送
        try:
            push_result = await self._push_provider.send(
                user_id=user_id,
                title=request.title,
                content=request.content or "",
            )
            message_id = push_result.get("message_id")
            status = "sent" if push_result.get("success") else "failed"
        except Exception as e:
            logger.error("[Notification] 推送发送失败: %s", str(e))
            message_id = None
            status = "failed"

        # 6. 记录推送历史
        push_record = PushRecord(
            user_id=user_id,
            notification_id=notification.id,
            push_type=push_type,
            device_token=request.device_token,
            status=status,
            sent_at=datetime.now(timezone.utc) if status == "sent" else None,
            error_message=None if status == "sent" else "推送发送失败",
        )
        db.add(push_record)

        # 7. 记录推送频率
        await self._record_push_frequency(user_id, push_type)

        await db.commit()

        return PushResult(
            success=status == "sent",
            message_id=message_id,
            notification_id=notification.id,
            error_message=None if status == "sent" else "推送发送失败",
        )

    async def _is_push_enabled(self, user_id: str, push_type: str) -> bool:
        """检查用户是否开启了指定类型的推送。

        Args:
            user_id: 用户ID
            push_type: 推送类型

        Returns:
            是否开启
        """
        # 先从 Redis 缓存获取
        settings_key = REDIS_KEY_NOTIFICATION_SETTINGS.format(user_id=user_id)
        cached = await self._redis.get(settings_key)

        if cached:
            settings = json.loads(cached)
            if not settings.get("push_enabled", True):
                return False
            return settings.get("types_enabled", {}).get(push_type, True)

        # 缓存不存在，使用默认设置
        # 危机干预推送强制开启
        if push_type in [NotificationType.CRISIS_ALERT, NotificationType.CRISIS_FOLLOW]:
            return True

        return push_type in DEFAULT_ENABLED_TYPES

    async def _check_push_frequency(self, user_id: str, push_type: str) -> bool:
        """检查推送频率是否超限。

        Args:
            user_id: 用户ID
            push_type: 推送类型

        Returns:
            是否允许推送
        """
        # 危机干预推送不受频率限制
        if push_type in [NotificationType.CRISIS_ALERT, NotificationType.CRISIS_FOLLOW]:
            return True

        # 获取频率配置
        config = self._get_frequency_config(push_type)
        if not config:
            return True

        key = REDIS_KEY_PUSH_FREQUENCY.format(user_id=user_id, push_type=push_type)
        current_count = await self._redis.get(key)

        if current_count is None:
            return True

        return int(current_count) < config["max_count"]

    async def _record_push_frequency(self, user_id: str, push_type: str) -> None:
        """记录推送频率。

        Args:
            user_id: 用户ID
            push_type: 推送类型
        """
        config = self._get_frequency_config(push_type)
        if not config:
            return

        key = REDIS_KEY_PUSH_FREQUENCY.format(user_id=user_id, push_type=push_type)
        current = await self._redis.get(key)

        if current is None:
            await self._redis.setex(key, config["window_seconds"], 1)
        else:
            await self._redis.incr(key)

    def _get_frequency_config(self, push_type: str) -> dict[str, int] | None:
        """获取推送类型的频率配置。

        Args:
            push_type: 推送类型

        Returns:
            频率配置，包含 max_count 和 window_seconds
        """
        configs = {
            NotificationType.CRISIS_ALERT: PushFrequencyConfig.CRISIS_LIMITS,
            NotificationType.CRISIS_FOLLOW: PushFrequencyConfig.CRISIS_LIMITS,
            NotificationType.AI_CARE: PushFrequencyConfig.AI_CARE_LIMITS,
            NotificationType.FRIEND_REQUEST: PushFrequencyConfig.FRIEND_REQUEST_LIMITS,
            NotificationType.FRIEND_ACCEPT: PushFrequencyConfig.FRIEND_REQUEST_LIMITS,
            NotificationType.TREEHOLE_REPLY: PushFrequencyConfig.SOCIAL_LIMITS,
            NotificationType.SQUARE_COMMENT: PushFrequencyConfig.SOCIAL_LIMITS,
            NotificationType.SQUARE_LIKE: PushFrequencyConfig.SOCIAL_LIMITS,
            NotificationType.SYSTEM: PushFrequencyConfig.SYSTEM_LIMITS,
            NotificationType.UPDATE: PushFrequencyConfig.SYSTEM_LIMITS,
            NotificationType.WEEKLY_REPORT: PushFrequencyConfig.SYSTEM_LIMITS,
        }
        return configs.get(push_type)

    async def _try_merge_notification(
        self,
        request: PushRequest,
        db: AsyncSession,
    ) -> Any | None:
        """尝试合并通知。

        5 分钟内同类通知合并为一条，保留最新内容，计数累加。

        Args:
            request: 推送请求
            db: 数据库会话

        Returns:
            合并后的通知，如果未合并返回 None
        """
        # 危机干预推送不合并
        if request.notification_type in [NotificationType.CRISIS_ALERT, NotificationType.CRISIS_FOLLOW]:
            return None

        user_id = request.user_id
        push_type = request.notification_type
        now = datetime.now(timezone.utc)

        # 查找最近的同类未读通知
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.type == push_type,
                Notification.is_read == False,  # noqa: E712
            )
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        # 检查是否在合并窗口内
        time_diff = (now - notification.created_at).total_seconds()
        if time_diff > PushFrequencyConfig.MERGE_WINDOW_SECONDS:
            return None

        # 合并：更新内容，累加计数
        merged_count = 2  # 第一次合并：原始通知(1) + 新通知(1)
        if notification.payload and "merged_count" in notification.payload:
            merged_count = notification.payload["merged_count"] + 1

        notification.title = request.title
        notification.content = request.content
        notification.payload = {
            **(request.payload or {}),
            "merged_count": merged_count,
            "last_merged_at": now.isoformat(),
        }
        notification.updated_at = now

        await db.flush()

        return type("MergedResult", (), {
            "notification_id": notification.id,
            "merged_count": merged_count,
        })()

    # =========================================================================
    # 通知设置
    # =========================================================================

    async def get_settings(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> NotificationSettingResponse:
        """获取用户通知设置。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            通知设置
        """
        # 先从 Redis 缓存获取
        settings_key = REDIS_KEY_NOTIFICATION_SETTINGS.format(user_id=user_id)
        cached = await self._redis.get(settings_key)

        if cached:
            settings = json.loads(cached)
            return NotificationSettingResponse(
                push_enabled=settings.get("push_enabled", True),
                types_enabled=settings.get("types_enabled", self._get_default_types_enabled()),
            )

        # 从用户表获取
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 从 notification_settings 字段获取
        settings_data = user.notification_settings or {}
        types_enabled = settings_data.get("types_enabled", self._get_default_types_enabled())

        response = NotificationSettingResponse(
            push_enabled=settings_data.get("push_enabled", True),
            types_enabled=types_enabled,
        )

        # 缓存到 Redis
        await self._redis.setex(
            settings_key,
            3600,  # 1 小时缓存
            json.dumps({
                "push_enabled": response.push_enabled,
                "types_enabled": response.types_enabled,
            }),
        )

        return response

    async def update_settings(
        self,
        user_id: str,
        request: NotificationSettingUpdateRequest,
        db: AsyncSession,
    ) -> NotificationSettingResponse:
        """更新用户通知设置。

        Args:
            user_id: 用户ID
            request: 更新请求
            db: 数据库会话

        Returns:
            更新后的设置
        """
        # 获取当前设置
        current = await self.get_settings(user_id, db)

        # 合并更新
        push_enabled = request.push_enabled if request.push_enabled is not None else current.push_enabled
        types_enabled = request.types_enabled if request.types_enabled is not None else current.types_enabled

        # 危机干预推送不能关闭
        types_enabled[NotificationType.CRISIS_ALERT] = True
        types_enabled[NotificationType.CRISIS_FOLLOW] = True

        # 更新用户表
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        user.notification_settings = {
            "push_enabled": push_enabled,
            "types_enabled": types_enabled,
        }
        await db.commit()

        # 更新 Redis 缓存
        settings_key = REDIS_KEY_NOTIFICATION_SETTINGS.format(user_id=user_id)
        await self._redis.setex(
            settings_key,
            3600,
            json.dumps({
                "push_enabled": push_enabled,
                "types_enabled": types_enabled,
            }),
        )

        return NotificationSettingResponse(
            push_enabled=push_enabled,
            types_enabled=types_enabled,
        )

    def _get_default_types_enabled(self) -> dict[str, bool]:
        """获取默认的通知类型开关。

        Returns:
            默认开关配置
        """
        types_enabled = {t: True for t in DEFAULT_ENABLED_TYPES}
        types_enabled.update({t: False for t in DEFAULT_DISABLED_TYPES})
        return types_enabled

    # =========================================================================
    # 工具方法
    # =========================================================================

    async def clear_settings_cache(self, user_id: str) -> None:
        """清除用户通知设置缓存。

        Args:
            user_id: 用户ID
        """
        settings_key = REDIS_KEY_NOTIFICATION_SETTINGS.format(user_id=user_id)
        await self._redis.delete(settings_key)

    async def get_unread_count(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """获取用户未读通知数。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            未读数量
        """
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
