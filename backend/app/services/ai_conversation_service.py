"""AI 对话服务层。

管理对话上下文、消息持久化、配额检查等业务逻辑。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import AIConversation, AIMessage
from app.services.ai_chat import (
    MockAIChat,
    GLMChatService,
    create_ai_chat_service,
)
from app.services.ai_config import get_greeting
from app.services.crisis_detection import CrisisDetector, CrisisLevel, get_crisis_detector
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 默认对话上下文轮数（1轮 = 1次用户 + 1次AI）
DEFAULT_MAX_CONTEXT_ROUNDS = 5

# 默认性格
DEFAULT_PERSONALITY = "xiaowen"


# ---------------------------------------------------------------------------
# AI 对话服务
# ---------------------------------------------------------------------------

class AIConversationService:
    """AI 对话服务，管理对话上下文和持久化。

    提供以下功能：
    - 同步对话（chat）
    - 流式对话（chat_stream）
    - 获取对话列表（get_conversations）
    - 获取开场白（get_greeting）
    - 对话上下文管理
    - 危机关键词检测
    - 配额检查

    使用示例：
        service = AIConversationService(db, settings)
        result = await service.chat(user_id, "你好", "xiaowen", None)
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
        daily_limit: int = 10,
        daily_limit_vip: int = 100,
        crisis_detector: CrisisDetector | None = None,
    ) -> None:
        """初始化 AI 对话服务。

        Args:
            db: 数据库会话
            ai_provider: AI 服务提供者（mock/glm_free/glm）
            zhipu_api_key: 智谱 API Key
            daily_limit: 普通用户每日对话限制
            daily_limit_vip: VIP 用户每日对话限制
            crisis_detector: 危机检测器（可选，默认使用全局实例）
        """
        self._db = db
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key
        self._daily_limit = daily_limit
        self._daily_limit_vip = daily_limit_vip
        self._crisis_detector = crisis_detector or get_crisis_detector()

        # AI 服务实例缓存（按性格区分）
        self._ai_services: dict[str, MockAIChat | GLMChatService] = {}

        logger.info(
            "[AIConversationService] 初始化完成，Provider: %s",
            ai_provider
        )

    def _get_ai_service(
        self,
        personality: str,
    ) -> MockAIChat | GLMChatService:
        """获取指定性格的 AI 服务实例。

        Args:
            personality: 性格标识

        Returns:
            AI 服务实例
        """
        if personality not in self._ai_services:
            self._ai_services[personality] = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                personality=personality,
            )
        return self._ai_services[personality]

    async def _get_or_create_conversation(
        self,
        user_id: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> AIConversation:
        """获取或创建对话。

        如果 conversation_id 存在，返回对应的对话；
        否则创建新对话。

        Args:
            user_id: 用户 ID
            personality: 性格标识
            conversation_id: 对话 ID（可选）

        Returns:
            AIConversation 对象

        Raises:
            AppError: 对话不存在或不属于当前用户
        """
        if conversation_id:
            # 查找现有对话
            stmt = (
                select(AIConversation)
                .where(
                    AIConversation.id == conversation_id,
                    AIConversation.user_id == user_id,
                    AIConversation.is_active == True,  # noqa: E712
                )
            )
            result = await self._db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise AppError(
                    code=ErrorCode.AI_CONVERSATION_NOT_FOUND,
                    message="对话不存在或已结束",
                    status_code=404,
                )

            return conversation

        # 创建新对话
        conversation = AIConversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ai_persona=personality,
            is_active=True,
            last_message_at=datetime.now(timezone.utc),
        )
        self._db.add(conversation)
        await self._db.flush()

        logger.info(
            "[AIConversationService] 创建新对话，ID: %s，性格: %s",
            conversation.id,
            personality
        )

        return conversation

    async def _get_context(
        self,
        conversation_id: str,
        max_rounds: int = DEFAULT_MAX_CONTEXT_ROUNDS,
    ) -> list[dict[str, str]]:
        """获取最近 N 轮对话上下文。

        1轮 = 1次用户消息 + 1次AI回复

        Args:
            conversation_id: 对话 ID
            max_rounds: 最大轮数

        Returns:
            对话历史列表，格式为 [{"role": "user/assistant", "content": "..."}]
        """
        # 查询最近的消息，按时间倒序
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(desc(AIMessage.created_at))
            .limit(max_rounds * 2)  # 每轮最多 2 条消息
        )
        result = await self._db.execute(stmt)
        messages = result.scalars().all()

        # 按时间正序排列（最早的在前）
        history = []
        for msg in reversed(messages):
            history.append({
                "role": msg.role,
                "content": msg.content,
            })

        return history

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        token_count: int | None = None,
    ) -> AIMessage:
        """保存消息到数据库。

        Args:
            conversation_id: 对话 ID
            role: 角色（user/assistant）
            content: 消息内容
            token_count: Token 消耗数（可选）

        Returns:
            AIMessage 对象
        """
        message = AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=token_count,
        )
        self._db.add(message)

        # 更新会话的最后消息时间
        stmt = (
            select(AIConversation)
            .where(AIConversation.id == conversation_id)
        )
        result = await self._db.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.last_message_at = datetime.now(timezone.utc)

        await self._db.flush()

        logger.debug(
            "[AIConversationService] 保存消息，对话: %s，角色: %s，长度: %d",
            conversation_id,
            role,
            len(content)
        )

        return message

    async def chat(
        self,
        user_id: str,
        message: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """同步对话。

        Args:
            user_id: 用户 ID
            message: 用户消息
            personality: 性格标识
            conversation_id: 对话 ID（可选）

        Returns:
            包含对话结果的字典：
            - conversation_id: 对话 ID
            - message: AI 回复
            - personality: 性格标识
        """
        # 获取或创建对话
        conversation = await self._get_or_create_conversation(
            user_id, personality, conversation_id
        )

        # 获取对话上下文
        history = await self._get_context(conversation.id)

        # 检测危机关键词
        crisis_result = self._crisis_detector.detect(message)
        if crisis_result:
            logger.warning(
                "[AIConversationService] 检测到危机信号，级别: %s",
                crisis_result["level"].value
            )

        # 保存用户消息
        await self._save_message(conversation.id, "user", message)

        # 调用 AI 服务
        ai_service = self._get_ai_service(personality)
        context = {"history": history} if history else None
        ai_response = await ai_service.chat(message, context)

        # 如果检测到危机，追加安全信息
        if crisis_result:
            safety_appendix = self._crisis_detector.get_safety_appendix(
                crisis_result["level"]
            )
            if safety_appendix:
                ai_response += safety_appendix

        # 保存 AI 回复
        await self._save_message(conversation.id, "assistant", ai_response)

        # 提交事务
        await self._db.commit()

        return {
            "conversation_id": conversation.id,
            "message": ai_response,
            "personality": personality,
        }

    async def chat_stream(
        self,
        user_id: str,
        message: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话（SSE 格式）。

        Args:
            user_id: 用户 ID
            message: 用户消息
            personality: 性格标识
            conversation_id: 对话 ID（可选）

        Yields:
            SSE 格式的文本片段：
            data: {"content": "xxx", "done": false}\\n\\n
            data: {"content": "", "done": true}\\n\\n
        """
        # 获取或创建对话
        conversation = await self._get_or_create_conversation(
            user_id, personality, conversation_id
        )

        # 获取对话上下文
        history = await self._get_context(conversation.id)

        # 检测危机关键词
        crisis_result = self._crisis_detector.detect(message)
        if crisis_result:
            logger.warning(
                "[AIConversationService] 流式对话检测到危机信号，级别: %s",
                crisis_result["level"].value
            )

        # 保存用户消息（在流式输出之前）
        await self._save_message(conversation.id, "user", message)
        await self._db.commit()  # 提交用户消息

        # 调用 AI 流式服务
        ai_service = self._get_ai_service(personality)
        context = {"history": history} if history else None

        # 收集完整响应用于保存
        full_response = []

        try:
            async for sse_chunk in ai_service.chat_stream(message, context):
                # 解析 SSE 数据
                if sse_chunk.startswith("data: "):
                    data_str = sse_chunk[6:].strip()
                    if data_str:
                        try:
                            chunk_data = json.loads(data_str)
                            content = chunk_data.get("content", "")
                            if content:
                                full_response.append(content)
                        except json.JSONDecodeError:
                            pass

                # 原样转发 SSE 数据
                yield sse_chunk

        except Exception as e:
            logger.error(
                "[AIConversationService] 流式对话异常: %s",
                str(e)
            )
            # 发送错误消息
            error_data = json.dumps(
                {"content": "抱歉，AI服务出现问题，请稍后重试。", "done": True},
                ensure_ascii=False
            )
            yield f"data: {error_data}\n\n"
            return

        # 流结束后追加危机安全信息（如果有）
        if crisis_result:
            safety_appendix = self._crisis_detector.get_safety_appendix(
                crisis_result["level"]
            )
            if safety_appendix:
                for char in safety_appendix:
                    sse_data = json.dumps(
                        {"content": char, "done": False},
                        ensure_ascii=False
                    )
                    yield f"data: {sse_data}\n\n"

                full_response.append(safety_appendix)

        # 保存完整的 AI 回复
        complete_response = "".join(full_response)
        await self._save_message(conversation.id, "assistant", complete_response)
        await self._db.commit()

        logger.info(
            "[AIConversationService] 流式对话完成，对话: %s，回复长度: %d",
            conversation.id,
            len(complete_response)
        )

    async def get_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取用户的对话列表。

        Args:
            user_id: 用户 ID
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            包含对话列表的字典：
            - items: 对话列表
            - total: 总数
            - page: 当前页码
            - page_size: 每页数量
        """
        # 查询对话数量
        count_stmt = (
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.is_active == True,  # noqa: E712
            )
        )
        count_result = await self._db.execute(count_stmt)
        total = len(count_result.all())

        # 查询对话列表
        offset = (page - 1) * page_size
        stmt = (
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.is_active == True,  # noqa: E712
            )
            .order_by(desc(AIConversation.last_message_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await self._db.execute(stmt)
        conversations = result.scalars().all()

        # 构建返回数据
        items = []
        for conv in conversations:
            # 获取最后一条消息预览
            last_msg_stmt = (
                select(AIMessage)
                .where(AIMessage.conversation_id == conv.id)
                .order_by(desc(AIMessage.created_at))
                .limit(1)
            )
            last_msg_result = await self._db.execute(last_msg_stmt)
            last_message = last_msg_result.scalar_one_or_none()

            items.append({
                "id": conv.id,
                "personality": conv.ai_persona,
                "title": conv.title,
                "last_message": last_message.content[:100] if last_message else None,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "created_at": conv.created_at.isoformat(),
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_greeting(
        self,
        user_id: str,
        personality: str | None = None,
    ) -> dict[str, Any]:
        """获取 AI 开场白。

        如果用户有活跃对话，返回上次对话的性格；
        否则创建新对话并返回开场白。

        Args:
            user_id: 用户 ID
            personality: 性格标识（可选，默认使用上次或默认性格）

        Returns:
            包含开场白的字典：
            - greeting: 开场白内容
            - personality: 性格标识
            - conversation_id: 对话 ID
        """
        # 如果未指定性格，查找上次使用的性格
        if not personality:
            last_conv_stmt = (
                select(AIConversation)
                .where(
                    AIConversation.user_id == user_id,
                    AIConversation.is_active == True,  # noqa: E712
                )
                .order_by(desc(AIConversation.last_message_at))
                .limit(1)
            )
            last_conv_result = await self._db.execute(last_conv_stmt)
            last_conv = last_conv_result.scalar_one_or_none()

            if last_conv:
                personality = last_conv.ai_persona
            else:
                personality = DEFAULT_PERSONALITY

        # 获取开场白
        greeting_text = get_greeting(personality)

        # 创建新对话
        conversation = await self._get_or_create_conversation(
            user_id, personality, None
        )

        # 如果是全新对话，保存开场白作为第一条 AI 消息
        # 检查是否已有消息
        msg_count_stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.id)
        )
        msg_count_result = await self._db.execute(msg_count_stmt)
        existing_messages = msg_count_result.all()

        if not existing_messages:
            await self._save_message(conversation.id, "assistant", greeting_text)

        await self._db.commit()

        return {
            "greeting": greeting_text,
            "personality": personality,
            "conversation_id": conversation.id,
        }

    async def check_quota(self, user_id: str, is_vip: bool = False) -> dict[str, Any]:
        """检查用户的对话配额。

        Args:
            user_id: 用户 ID
            is_vip: 是否为 VIP 用户

        Returns:
            包含配额信息的字典：
            - daily_limit: 每日限制
            - used: 已使用次数
            - remaining: 剩余次数
            - can_chat: 是否可以继续对话
        """
        # 这里需要实现 Redis 计数逻辑
        # 目前简化处理，直接返回限制信息
        daily_limit = self._daily_limit_vip if is_vip else self._daily_limit

        # TODO: 从 Redis 获取当日已使用次数
        used = 0

        return {
            "daily_limit": daily_limit,
            "used": used,
            "remaining": daily_limit - used,
            "can_chat": used < daily_limit,
        }
