"""危机干预服务模块。

提供危机事件管理相关的核心业务逻辑：
- 危机事件列表（优先级排序）
- 危机事件详情（含用户历史危机统计）
- 人工介入标记
- 处理状态更新
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import (
    and_,
    desc,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.admin import Admin
from app.models.ai import AIMessage, AIConversation
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.report import (
    AdminCrisisDetail,
    AdminCrisisListItem,
    AdminCrisisListRequest,
    AdminCrisisResolveRequest,
    AdminCrisisResolveResponse,
    CrisisLevel,
    CrisisStatus,
)

logger = logging.getLogger(__name__)


# 危机级别优先级权重（数值越大优先级越高）
CRISIS_LEVEL_PRIORITY = {
    CrisisLevel.HIGH.value: 100,
    CrisisLevel.MEDIUM.value: 50,
    CrisisLevel.LOW.value: 10,
}


class AdminCrisisService:
    """危机干预服务。

    封装危机事件管理的核心业务逻辑。
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # -----------------------------------------------------------------------
    # 危机事件列表
    # -----------------------------------------------------------------------

    async def get_crisis_events(
        self,
        db: AsyncSession,
        params: AdminCrisisListRequest,
    ) -> PaginatedResponse[AdminCrisisListItem]:
        """查询危机事件列表。

        按危机级别和时间综合排序（高危事件优先）。

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            分页危机事件列表
        """
        # 构建基础查询（查询有危机标记的消息）
        stmt = select(AIMessage).where(
            AIMessage.crisis_level.isnot(None),
        )

        # 应用筛选条件
        if params.level:
            stmt = stmt.where(AIMessage.crisis_level == params.level.value)
        if params.status:
            # 根据危机状态字段筛选（已添加 crisis_status 字段）
            stmt = stmt.where(AIMessage.crisis_status == params.status.value)
        if params.user_id:
            # 需要关联会话表获取用户ID
            conv_subquery = select(AIConversation.id).where(
                AIConversation.user_id == params.user_id,
            )
            stmt = stmt.where(AIMessage.conversation_id.in_(conv_subquery))
        if params.start_time:
            stmt = stmt.where(AIMessage.created_at >= params.start_time)
        if params.end_time:
            stmt = stmt.where(AIMessage.created_at <= params.end_time)

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 按危机级别和时间排序（高危优先）
        # 使用 CASE 语句实现自定义排序
        priority_order = func.case(
            (AIMessage.crisis_level == CrisisLevel.HIGH.value, 3),
            (AIMessage.crisis_level == CrisisLevel.MEDIUM.value, 2),
            (AIMessage.crisis_level == CrisisLevel.LOW.value, 1),
            else_=0,
        )

        if params.sort_order == "desc":
            stmt = stmt.order_by(desc(priority_order), desc(AIMessage.created_at))
        else:
            stmt = stmt.order_by(priority_order, AIMessage.created_at)

        # 分页
        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        # 执行查询
        result = await db.execute(stmt)
        messages = result.scalars().all()

        # 查询关联数据
        event_data = await self._enrich_crisis_events(db, messages)

        return PaginatedResponse.create(
            data=event_data,
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def _enrich_crisis_events(
        self,
        db: AsyncSession,
        messages: list[AIMessage],
    ) -> list[AdminCrisisListItem]:
        """丰富危机事件数据。

        查询关联的用户信息、会话信息等，并正确判断危机状态。

        Args:
            db: 数据库会话
            messages: 消息列表

        Returns:
            丰富后的危机事件列表
        """
        if not messages:
            return []

        # 获取会话信息
        conv_ids = {m.conversation_id for m in messages}
        conv_stmt = select(AIConversation).where(AIConversation.id.in_(conv_ids))
        conv_result = await db.execute(conv_stmt)
        conversations = {c.id: c for c in conv_result.scalars().all()}

        # 获取用户信息
        user_ids = {c.user_id for c in conversations.values() if c.user_id}
        user_stmt = select(User).where(User.id.in_(user_ids))
        user_result = await db.execute(user_stmt)
        users = {u.id: u for u in user_result.scalars().all()}

        # 获取处理人信息
        processor_ids = {m.crisis_resolved_by for m in messages if m.crisis_resolved_by}
        admin_names = {}
        if processor_ids:
            admin_stmt = select(Admin.id, Admin.nickname).where(Admin.id.in_(processor_ids))
            admin_result = await db.execute(admin_stmt)
            admin_names = {row[0]: row[1] for row in admin_result.all()}

        # 构建响应数据
        data = []
        for msg in messages:
            conv = conversations.get(msg.conversation_id)
            user = users.get(conv.user_id) if conv else None

            # 解析关键词
            keywords = []
            if msg.crisis_keywords:
                keywords = [kw.strip() for kw in msg.crisis_keywords.split(",") if kw.strip()]

            # 根据危机状态字段判断处理状态
            # 如果有 crisis_status 字段，使用该字段；否则根据其他字段判断
            status = self._determine_crisis_status(msg)

            data.append(AdminCrisisListItem(
                id=msg.id,
                user_id=conv.user_id if conv else "",
                user_nickname=user.nickname if user else None,
                user_phone=self._mask_phone(user.phone) if user else None,
                conversation_id=msg.conversation_id,
                ai_persona=conv.ai_persona if conv else None,
                level=msg.crisis_level or CrisisLevel.LOW.value,
                keywords=keywords,
                status=status,
                resolved_by=msg.crisis_resolved_by,
                resolved_by_name=admin_names.get(msg.crisis_resolved_by),
                resolved_at=msg.crisis_resolved_at,
                created_at=msg.created_at,
            ))

        return data

    @staticmethod
    def _determine_crisis_status(msg: AIMessage) -> str:
        """判断危机事件状态。

        基于 crisis_status、crisis_resolved_at 等字段综合判断。

        Args:
            msg: AI 消息对象

        Returns:
            危机状态字符串
        """
        # 如果有 crisis_status 字段，直接使用
        if hasattr(msg, "crisis_status") and msg.crisis_status:
            return msg.crisis_status

        # 兼容旧数据：根据其他字段判断
        if msg.crisis_resolved_at:
            return CrisisStatus.RESOLVED.value
        if msg.crisis_level is None:
            # 如果危机级别被清除，可能是误报
            return CrisisStatus.FALSE_POSITIVE.value

        return CrisisStatus.PENDING.value

    # -----------------------------------------------------------------------
    # 危机事件详情
    # -----------------------------------------------------------------------

    async def get_crisis_detail(
        self,
        db: AsyncSession,
        message_id: str | UUID,
    ) -> AdminCrisisDetail:
        """获取危机事件详情。

        包含用户历史危机统计。

        Args:
            db: 数据库会话
            message_id: 消息ID

        Returns:
            危机事件详情

        Raises:
            AppError: 危机事件不存在时抛出
        """
        # 查询消息
        stmt = select(AIMessage).where(
            AIMessage.id == message_id,
            AIMessage.crisis_level.isnot(None),
        )
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise AppError(
                code=ErrorCode.CRISIS_EVENT_NOT_FOUND,
                message="危机事件不存在",
                status_code=404,
            )

        # 查询会话信息
        conv_stmt = select(AIConversation).where(AIConversation.id == message.conversation_id)
        conv_result = await db.execute(conv_stmt)
        conversation = conv_result.scalar_one_or_none()

        # 查询用户信息
        user = None
        if conversation and conversation.user_id:
            user_stmt = select(User).where(User.id == conversation.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

        # 解析关键词
        keywords = []
        if message.crisis_keywords:
            keywords = [kw.strip() for kw in message.crisis_keywords.split(",") if kw.strip()]

        # 查询用户历史危机统计
        user_crisis_history = {}
        if user:
            user_crisis_history = await self._get_user_crisis_history(db, user.id)

        # 获取 AI 回复（下一条消息）
        ai_response = await self._get_ai_response(db, message.conversation_id, message.created_at)

        # 获取处理人信息
        admin_names = {}
        if hasattr(message, "crisis_resolved_by") and message.crisis_resolved_by:
            admin_stmt = select(Admin.id, Admin.nickname).where(Admin.id == message.crisis_resolved_by)
            admin_result = await db.execute(admin_stmt)
            admin_row = admin_result.first()
            if admin_row:
                admin_names[admin_row[0]] = admin_row[1]

        return AdminCrisisDetail(
            id=message.id,
            user_id=conversation.user_id if conversation else "",
            user_nickname=user.nickname if user else None,
            user_phone=self._mask_phone(user.phone) if user else None,
            user_age_range=user.age_range if user else None,
            user_is_minor=user.is_minor if user else False,
            conversation_id=message.conversation_id,
            ai_persona=conversation.ai_persona if conversation else None,
            message_content=self._mask_content(message.content) if message.content else None,
            level=message.crisis_level or CrisisLevel.LOW.value,
            keywords=keywords,
            ai_response=ai_response,
            status=self._determine_crisis_status(message),
            resolution_note=message.crisis_resolution_note,
            resolved_by=message.crisis_resolved_by,
            resolved_by_name=admin_names.get(message.crisis_resolved_by) if hasattr(message, "crisis_resolved_by") else None,
            resolved_at=message.crisis_resolved_at,
            created_at=message.created_at,
            user_crisis_history=user_crisis_history,
        )

    async def _get_user_crisis_history(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> dict[str, Any]:
        """获取用户危机历史统计。

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            危机历史统计
        """
        # 获取用户所有会话
        conv_stmt = select(AIConversation.id).where(AIConversation.user_id == user_id)
        conv_result = await db.execute(conv_stmt)
        conv_ids = [row[0] for row in conv_result.all()]

        if not conv_ids:
            return {}

        # 统计危机事件数量
        # 总危机事件数
        total_stmt = select(func.count()).select_from(AIMessage).where(
            AIMessage.conversation_id.in_(conv_ids),
            AIMessage.crisis_level.isnot(None),
        )
        total_result = await db.execute(total_stmt)
        total_count = total_result.scalar() or 0

        # 按级别统计
        level_stmt = (
            select(
                AIMessage.crisis_level,
                func.count().label("count"),
            )
            .where(
                AIMessage.conversation_id.in_(conv_ids),
                AIMessage.crisis_level.isnot(None),
            )
            .group_by(AIMessage.crisis_level)
        )
        level_result = await db.execute(level_stmt)
        level_distribution = {row[0]: row[1] for row in level_result.all()}

        # 最近30天危机事件数
        month_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_stmt = select(func.count()).select_from(AIMessage).where(
            AIMessage.conversation_id.in_(conv_ids),
            AIMessage.crisis_level.isnot(None),
            AIMessage.created_at >= month_ago,
        )
        recent_result = await db.execute(recent_stmt)
        recent_count = recent_result.scalar() or 0

        # 最近一次危机时间
        last_stmt = (
            select(AIMessage.created_at)
            .where(
                AIMessage.conversation_id.in_(conv_ids),
                AIMessage.crisis_level.isnot(None),
            )
            .order_by(desc(AIMessage.created_at))
            .limit(1)
        )
        last_result = await db.execute(last_stmt)
        last_crisis = last_result.scalar_one_or_none()

        return {
            "total_count": total_count,
            "recent_30_days_count": recent_count,
            "level_distribution": level_distribution,
            "last_crisis_at": last_crisis.isoformat() if last_crisis else None,
        }

    async def _get_ai_response(
        self,
        db: AsyncSession,
        conversation_id: str,
        after_time: datetime,
    ) -> str | None:
        """获取 AI 回复内容。

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            after_time: 用户消息时间

        Returns:
            AI 回复内容
        """
        stmt = (
            select(AIMessage.content)
            .where(
                AIMessage.conversation_id == conversation_id,
                AIMessage.role == "assistant",
                AIMessage.created_at > after_time,
            )
            .order_by(AIMessage.created_at)
            .limit(1)
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        return content

    # -----------------------------------------------------------------------
    # 危机事件处理
    # -----------------------------------------------------------------------

    async def resolve_crisis(
        self,
        db: AsyncSession,
        message_id: str | UUID,
        request: AdminCrisisResolveRequest,
        admin_id: str,
        ip_address: str | None = None,
        log_action: Any = None,
    ) -> AdminCrisisResolveResponse:
        """处理危机事件。

        Args:
            db: 数据库会话
            message_id: 消息ID
            request: 处理请求
            admin_id: 管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            处理结果

        Raises:
            AppError: 危机事件不存在或已处理时抛出
        """
        # 查询消息
        stmt = select(AIMessage).where(
            AIMessage.id == message_id,
            AIMessage.crisis_level.isnot(None),
        )
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise AppError(
                code=ErrorCode.CRISIS_EVENT_NOT_FOUND,
                message="危机事件不存在",
                status_code=404,
            )

        # 检查危机事件是否已被处理
        current_status = self._determine_crisis_status(message)
        if current_status in [CrisisStatus.RESOLVED.value, CrisisStatus.FALSE_POSITIVE.value]:
            raise AppError(
                code=ErrorCode.CRISIS_ALREADY_RESOLVED,
                message="该危机事件已处理",
                status_code=400,
            )

        now = datetime.now(timezone.utc)

        # 更新危机状态和处理信息
        message.crisis_status = request.status
        message.crisis_resolved_by = admin_id
        message.crisis_resolution_note = request.note
        message.crisis_resolved_at = now

        if request.status == "false_positive":
            # 标记为误报，可选择清除危机标记
            message.crisis_level = None
            message.crisis_keywords = None

        # 记录审计日志
        if log_action:
            await log_action(
                db=db,
                admin_id=admin_id,
                action="resolve_crisis",
                target_type="crisis_event",
                target_id=str(message_id),
                details={
                    "status": request.status,
                    "note": request.note,
                    "notify_user": request.notify_user,
                    "original_level": message.crisis_level,
                },
                ip_address=ip_address,
                auto_commit=False,
            )

        await db.commit()

        logger.info(
            "处理危机事件: message_id=%s, status=%s, admin_id=%s",
            message_id,
            request.status,
            admin_id,
        )

        # TODO: 如果需要联系用户，触发通知
        # if request.notify_user:
        #     await self._notify_user_for_crisis(db, message)

        return AdminCrisisResolveResponse(
            id=message.id,
            status=request.status,
            message=f"危机事件已标记为{'已解决' if request.status == 'resolved' else '误报'}",
        )

    # -----------------------------------------------------------------------
    # 工具方法
    # -----------------------------------------------------------------------

    @staticmethod
    def _mask_phone(phone: str | None) -> str | None:
        """手机号脱敏处理。"""
        if not phone or len(phone) < 7:
            return phone
        return f"{phone[:3]}****{phone[-4:]}"

    @staticmethod
    def _mask_content(content: str | None, max_length: int = 100) -> str | None:
        """内容脱敏处理（截断）。"""
        if not content:
            return None
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    async def mark_human_intervention(
        self,
        db: AsyncSession,
        message_id: str | UUID,
        admin_id: str,
        ip_address: str | None = None,
        log_action: Any = None,
    ) -> dict[str, Any]:
        """标记人工介入。

        用于标记正在处理的危机事件，将状态更新为 intervening。

        Args:
            db: 数据库会话
            message_id: 消息ID
            admin_id: 管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            操作结果
        """
        # 查询消息
        stmt = select(AIMessage).where(
            AIMessage.id == message_id,
            AIMessage.crisis_level.isnot(None),
        )
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise AppError(
                code=ErrorCode.CRISIS_EVENT_NOT_FOUND,
                message="危机事件不存在",
                status_code=404,
            )

        # 检查危机事件是否已被处理
        current_status = self._determine_crisis_status(message)
        if current_status in [CrisisStatus.RESOLVED.value, CrisisStatus.FALSE_POSITIVE.value]:
            raise AppError(
                code=ErrorCode.CRISIS_ALREADY_RESOLVED,
                message="该危机事件已处理，无法标记人工介入",
                status_code=400,
            )

        # 更新危机状态为人工介入中
        message.crisis_status = CrisisStatus.INTERVENING.value
        message.crisis_resolved_by = admin_id

        # 记录审计日志
        if log_action:
            await log_action(
                db=db,
                admin_id=admin_id,
                action="mark_crisis_intervention",
                target_type="crisis_event",
                target_id=str(message_id),
                details={
                    "level": message.crisis_level,
                    "keywords": message.crisis_keywords,
                    "previous_status": current_status,
                },
                ip_address=ip_address,
                auto_commit=False,
            )

        await db.commit()

        logger.info(
            "标记人工介入: message_id=%s, admin_id=%s, previous_status=%s",
            message_id,
            admin_id,
            current_status,
        )

        return {
            "id": str(message_id),
            "status": CrisisStatus.INTERVENING.value,
            "message": "已标记为人工介入中",
        }
